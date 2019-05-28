import io
import base64
from odoo import api, models, _
from ...queue_job.job import job
from odoo.tools import pycompat
from datetime import datetime, timedelta
from ...connector_voicent.examples import voicent
import tempfile
import shutil


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @job
    @api.multi
    def check_status_job(self):
        for rec in self:
            queue_job = self.env['queue.job'].search(
                [('uuid', '=', self._context.get('job_uuid'))])
            voicent_obj = voicent.Voicent(
                queue_job.call_line_id.backend_id.host,
                str(queue_job.call_line_id.backend_id.port))
            status = voicent_obj.checkStatus(queue_job.voicent_campaign)
            queue_job.helpdesk_ticket_id.message_post(
                body=_('Status Call on <b>%s</b>: <b>%s</b>' %
                       (queue_job.call_line_id.backend_id.port,
                        status)))
            if status != 'OK':
                next_time = datetime.now() + timedelta(minutes=15)
                rec.with_delay(eta=next_time).check_status_job()
            if queue_job.state == 'failed':
                message = _("""Job has been failed, Please check the:
                    <a href=# data-oe-model=queue.job data-oe-id=%d>%s</a> job
                            and fix the issue and re-execute the job"""
                            ) % (queue_job.id, queue_job.name)
                queue_job.helpdesk_ticket_id.message_post(body=message)

    @job
    @api.multi
    def voicent_import_and_runcampaign(self):
        for rec in self:
            queue_job = self.env['queue.job'].search(
                [('uuid', '=', self._context.get('job_uuid'))])

            if queue_job.call_line_id.helpdesk_ticket_stage_id.id \
                    == queue_job.helpdesk_ticket_id.stage_id.id:
                fp = io.BytesIO()
                writer = pycompat.csv_writer(fp, quoting=1)
                writer.writerow(("name", "phone"))
                writer.writerow(
                    [queue_job.helpdesk_ticket_id.partner_id.name,
                     queue_job.helpdesk_ticket_id.partner_id.phone])
                self.env['ir.attachment'].create({
                    'name': queue_job.name,
                    'datas': base64.encodestring(fp.getvalue()),
                    'datas_fname': "%s.csv" % (queue_job.name),
                    'res_model': 'queue.job',
                    'res_id': queue_job.id})
                directory_name = tempfile.mkdtemp(suffix='tempimagenew')
                file_name = directory_name + "/" + queue_job.name + ".csv"
                write_file = open(file_name, 'wb')
                write_file.write(fp.getvalue())
                voicent_obj = voicent.Voicent(
                    queue_job.call_line_id.backend_id.host,
                    str(queue_job.call_line_id.backend_id.port))
                imp_run_camp = voicent_obj.importAndRunCampaign(
                    file_name, "tts",
                    queue_job.call_line_id.voicent_app)
                write_file.close()
                shutil.rmtree(directory_name)
                queue_job.helpdesk_ticket_id.message_post(
                    body=_('Call has been sent to <b>%s</b>' %
                           (queue_job.call_line_id.backend_id.host)))
                new_job = rec.with_delay().check_status_job()
                db_job = new_job.db_record()
                if db_job:
                    db_job.write(
                        {'voicent_campaign': imp_run_camp.get('camp_id'),
                         'helpdesk_ticket_id': queue_job.helpdesk_ticket_id.id,
                         'call_line_id': queue_job.call_line_id.id})
            else:
                queue_job.state = 'done'
            if queue_job.state == 'failed':
                message = _("""Job has been failed, Please check the:
                    <a href=# data-oe-model=queue.job data-oe-id=%d>%s</a> job
                            and fix the issue and re-execute the job."""
                            ) % (queue_job.id, queue_job.name)
                queue_job.helpdesk_ticket_id.message_post(body=message)

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('stage_id') and rec.partner_id.company_type and \
                    rec.partner_id.can_call:
                call_lines = self.env['backend.voicent.call.line'].search(
                    [('helpdesk_ticket_stage_id', '=',
                      vals.get('stage_id')),
                     ('backend_id.is_active', '=', True)])
                for line_rec in call_lines:
                    q_job = rec.with_delay(
                        eta=line_rec.backend_id.next_call). \
                        voicent_import_and_runcampaign()
                    db_job = q_job.db_record()
                    if db_job:
                        db_job.write({'helpdesk_ticket_id': rec.id,
                                      'call_line_id': line_rec.id})
        return super(HelpdeskTicket, self).write(vals)
