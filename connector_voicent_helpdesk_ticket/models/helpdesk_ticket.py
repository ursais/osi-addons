# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import hashlib
import io
import shutil
import tempfile
import time
from voicent import voicent
from odoo import api, fields, models, _
from odoo.tools import pycompat
from ...queue_job.job import job
from ...queue_job.exception import RetryableJobError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    call_count = fields.Integer(string='Call count', default=0)

    def generate_identity(self):
        hasher = hashlib.sha1()
        hasher.update(self.id)
        hasher.update(self.stage_id.id)
        return hasher.hexdigest()

    @api.multi
    def voicent_check_status(self, campaign, call_line):
        for rec in self:
            voicent_obj = voicent.Voicent(
                call_line.backend_id.host,
                str(call_line.backend_id.port),
                call_line.backend_id.callerid,
                str(call_line.backend_id.line))
            res = voicent_obj.checkStatus(campaign)
            i = 1
            # Wait for the campaign to finish
            while res.get('status') != 'FINISHED':
                time.sleep(i)
                i += 2
                res = voicent_obj.checkStatus(campaign)
            filename = \
                str(rec.id) + '-' + str(rec.stage_id.id) + '-' + \
                fields.Datetime.now().strftime(
                    '%Y-%m-%d-%H-%M-%S') + '.csv'
            res2 = voicent_obj.exportResult(campaign, filename)
            i = 1
            # Wait to get the results
            while not (res2 and 'Notes' in res2):
                time.sleep(i)
                i += 1
                res2 = voicent_obj.exportResult(campaign, filename)
            # Post the response on the ticket
            message = _("""Status of campaign <b>%s</b> on <b>%s</b>:
             <b>%s</b>""" % (campaign,
                             call_line.backend_id.name,
                             res.get('status')))
            rec.message_post(body=message)
            # Execute the actions
            for reply in call_line.reply_ids:
                if reply.reply_field == 'notes':
                    field = res2['Notes']
                else:
                    field = res.get(reply.reply_field)
                if reply.reply_value in str(field):
                    ctx = dict(self.env.context or {})
                    ctx.update(
                        {'active_id': rec.id,
                         'active_model': 'helpdesk.ticket',
                         'call_line_id': call_line.id})
                    reply.action_id.with_context(ctx).run()

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
                if res.get('camp_id') and res.get('status') == 'OK':
                    rec.voicent_check_status(res.get('camp_id'), call_line)
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
                            eta=line_rec.backend_id.next_call,
                            identity_key=self.generate_identity).\
                            voicent_start_campaign(line_rec)
                        vals.update({'call_count': 0})
        return super().write(vals)
