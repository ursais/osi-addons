# Import Odoo libs
from odoo import fields, models, _
from markupsafe import Markup


class QueueJob(models.Model):
    """Inherit Queue Jobs to add Batch Functionality and activity creation."""

    _inherit = "queue.job"

    # METHODS #####

    def _message_post_on_failure(self):
        rec = super()._message_post_on_failure()
        for record in self:
            for mrp_batch in record.records:
                if mrp_batch.mrp_batch_id:
                    mrp_batch.mrp_batch_id.message_post(
                        body="Something bad happened during the execution of the Queue job. More details in the queue job."
                    )
                    to_do_activity_type_id = self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mail_activity_data_todo", raise_if_not_found=False
                    )
                    res_model_id = self.env["ir.model"]._get_id("mrp.production.batch")
                    date_deadline = fields.Date.today()
                    base_url = (
                        self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                    )
                    link_queue_job = Markup(
                        '<a href="{}/web#id={}&model={}&view_type=form" class="o_mail_redirect" data-oe-model="{}" data-oe-id="{}">{}</a>'
                    ).format(
                        base_url,
                        self.id,
                        self._name,
                        self._name,
                        self.id,
                        self.name or f"Queue Job #{self.id}",
                    )
                    content = _(
                        "Queue job %(link_queue_job)s failed. Please check this queue job for issues.",
                        link_queue_job=link_queue_job,
                    )
                    body = Markup("<p>%s</p>") % content
                    activity = self.env["mail.activity"].create(
                        {
                            "activity_type_id": to_do_activity_type_id,
                            "date_deadline": date_deadline,
                            "res_id": mrp_batch.mrp_batch_id.id,
                            "res_model_id": res_model_id,
                            "user_id": mrp_batch.mrp_batch_id.responsible_id.id,
                            "note": body,
                        }
                    )
        return rec

    def write(self, vals):
        res = super().write(vals)

        # Check if the job state has changed to 'done' or 'failed'
        if "state" in vals and vals.get("state") in ("done", "failed", "cancelled"):
            for job in self:
                # If the job is related to a manufacturing order, check its batch
                if job.model_name == "mrp.production" and job.records:
                    # Assuming there's only one record in the list
                    production = job.records[0]
                    if production.mrp_batch_id:
                        production.mrp_batch_id._check_and_update_queuing()

        return res

    # END #########
