# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import io
import base64
from odoo import api, models, _
from ...queue_job.job import job
from odoo.tools import pycompat
from ...connector_voicent.examples import voicent
import tempfile
import shutil


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @job
    @api.multi
    def check_status_job(self, voicent_campaign, helpdesk_ticket,
                         call_line):
        for rec in self:
            voicent_obj = voicent.Voicent(
                call_line.backend_id.host,
                str(call_line.backend_id.port),
                call_line.backend_id.callerid,
                str(call_line.backend_id.line))
            status = voicent_obj.checkStatus(voicent_campaign)
            message = _("""Status of campaign <b>%s</b> on <b>%s</b>:
             %s""" % (voicent_campaign,
                      call_line.backend_id.name,
                      status))
            helpdesk_ticket.message_post(body=message)

    @job
    @api.multi
    def voicent_import_and_runcampaign(self, helpdesk_ticket, call_line):
        for rec in self:
            if call_line.helpdesk_ticket_stage_id.id \
                    == helpdesk_ticket.stage_id.id:
                # Generate the CSV file
                fp = io.BytesIO()
                writer = pycompat.csv_writer(fp, quoting=1)
                writer.writerow(("Name", "Phone"))
                writer.writerow(
                    [helpdesk_ticket.partner_id.name,
                     helpdesk_ticket.partner_id.phone])
                directory = tempfile.mkdtemp(suffix='-helpdesk.ticket')
                file_name = directory + "/" + rec.name + rec.stage_id.name +\
                            ".csv"
                write_file = open(file_name, 'wb')
                write_file.write(fp.getvalue())
                write_file.close()
                # Contact Voicent
                voicent_obj = voicent.Voicent(
                    call_line.backend_id.host,
                    str(call_line.backend_id.port),
                    call_line.backend_id.callerid,
                    str(call_line.backend_id.line))
                res = voicent_obj.importAndRunCampaign(file_name, "tts",
                                                       call_line.voicent_app)
                # Attach the file to the ticket
                self.env['ir.attachment'].create({
                    'name': rec.name,
                    'datas': base64.encodestring(fp.getvalue()),
                    'datas_fname': "%s.csv" % (rec.name),
                    'res_model': 'helpdesk.ticket',
                    'res_id': rec.id})
                # Delete the file on the filesystem
                shutil.rmtree(directory)
                if res.get('camp_id'):
                    message = _("""Call has been sent to <b>%s</b>.
                    The campaign ID is <b>%s</b> and the status is: %s""" %
                                (call_line.backend_id.name,
                                 res.get('camp_id'),
                                 res.get('status')))
                    rec.with_delay().check_status_job(
                        res.get('camp_id'),
                        helpdesk_ticket,
                        call_line)
                else:
                    message = _("""Call has been sent to <b>%s</b> but failed
                     with the following message: %s""" %
                                (call_line.backend_id.name,
                                 res))
            else:
                message = _("Call has been cancelled because the stage has "
                            "changed.")
            helpdesk_ticket.message_post(body=message)

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('stage_id') and rec.partner_id.company_type and \
                    rec.partner_id.can_call:
                call_lines = self.env['backend.voicent.call.line'].search(
                    [('helpdesk_ticket_stage_id', '=',
                      vals.get('stage_id')),
                     ('backend_id.active', '=', True)])
                for line_rec in call_lines:
                    if not (line_rec.has_parent is True and
                            rec.parent_id is False):
                        rec.with_delay(
                            eta=line_rec.backend_id.next_call). \
                            voicent_import_and_runcampaign(rec, line_rec)
        return super(HelpdeskTicket, self).write(vals)
