# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import io
import shutil
import tempfile
from odoo import api, fields, models, _
from ...queue_job.job import job
from ...queue_job.exception import RetryableJobError
from odoo.tools import pycompat
from ...connector_voicent.examples import voicent


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    call_count = fields.Integer(string='Call count', default=0)

    @job
    @api.multi
    def voicent_check_status(self, campaign, call_line):
        for rec in self:
            voicent_obj = voicent.Voicent(
                call_line.backend_id.host,
                str(call_line.backend_id.port),
                call_line.backend_id.callerid,
                str(call_line.backend_id.line))
            res = voicent_obj.checkStatus(campaign)
            message = _("""Status of campaign <b>%s</b> on <b>%s</b>:
             <b>%s</b>""" % (campaign,
                             call_line.backend_id.name,
                             res.get('status')))
            rec.message_post(body=message)
            if res.get('status') == 'FINISHED':
                for reply in call_line.reply_ids:
                    if reply.reply_field == 'notes':
                        filename = \
                            str(rec.id) + '-' + str(rec.stage_id.id) + '-' + \
                            fields.Datetime.now().strftime(
                                '%Y-%m-%d-%H-%M-%S') + '.csv'
                        try:
                            res2 = voicent_obj.exportResult(campaign, filename)
                            field = res2['Notes']
                        except TypeError:
                            raise RetryableJobError(res2)
                    else:
                        field = res.get(reply.reply_field)
                    if reply.reply_value in str(field):
                        ctx = dict(self.env.context or {})
                        ctx.update(
                            {'active_id': rec.id,
                             'active_model': 'helpdesk.ticket'})
                        reply.action_id.with_context(ctx).run()
            else:
                raise RetryableJobError(res)

    @job
    @api.multi
    def voicent_start_campaign(self, call_line):
        for rec in self:
            if call_line.helpdesk_ticket_stage_id.id == rec.stage_id.id:
                # Generate the CSV file
                fp = io.BytesIO()
                writer = pycompat.csv_writer(fp, quoting=1)
                headers = []
                vals = []
                MailTemplate = self.env['mail.template']
                for field in call_line.contact_ids:
                    head = field.name
                    if head == 'Other':
                        head = field.other
                    lang = (rec.id and rec.partner_id.lang or "en_US")
                    value = \
                        MailTemplate.with_context(lang=lang)._render_template(
                            '${object.' + field.field_domain + '}',
                            'helpdesk.ticket',
                            rec.id)
                    if not value:
                        value = field.default_value
                    headers.append(head)
                    vals.append(value)
                writer.writerow(headers)
                writer.writerow(vals)
                directory = tempfile.mkdtemp(suffix='-helpdesk.ticket')
                file_name = \
                    directory + "/" + str(rec.id) + '-' + \
                    str(rec.stage_id.id) + '-' + \
                    fields.Datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + \
                    '.csv'
                write_file = open(file_name, 'wb')
                write_file.write(fp.getvalue())
                write_file.close()
                # Connect to Voicent
                voicent_obj = voicent.Voicent(call_line.backend_id.host,
                                              str(call_line.backend_id.port),
                                              call_line.backend_id.callerid,
                                              str(call_line.backend_id.line))
                res = voicent_obj.importAndRunCampaign(file_name,
                                                       call_line.msgtype,
                                                       call_line.msginfo)
                # Delete the file on the filesystem
                shutil.rmtree(directory)
                if res.get('camp_id'):
                    message = _("""Call has been sent to <b>%s</b>.
                    The campaign ID is <b>%s</b> and the status is:
                    <b>%s</b>""" % (call_line.backend_id.name,
                                    res.get('camp_id'),
                                    res.get('status')))
                    rec.message_post(body=message)
                    rec.with_delay().voicent_check_status(res.get('camp_id'),
                                                          call_line)
                else:
                    message = _("""Call has been sent to <b>%s</b> but failed
                    with the following message: <b>%s</b>""" %
                                (call_line.backend_id.name, res))
                    rec.message_post(body=message)
                    raise RetryableJobError(res)
            else:
                message = _("Call has been cancelled because the stage has "
                            "changed.")
                rec.message_post(body=message)

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('stage_id') and rec.partner_id.company_type and \
                    rec.partner_id.can_call:
                call_lines = self.env['backend.voicent.call.line'].search(
                    [('helpdesk_ticket_stage_id', '=', vals.get('stage_id')),
                     ('backend_id.active', '=', True)])
                for line_rec in call_lines:
                    if not (line_rec.has_parent is True and
                            rec.parent_id is False):
                        rec.with_delay(
                            eta=line_rec.backend_id.next_call). \
                            voicent_start_campaign(line_rec)
                        vals.update({'call_count': 0})
        return super().write(vals)
