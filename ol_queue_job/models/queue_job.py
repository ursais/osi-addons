import logging

_logger = logging.getLogger(__name__)

from odoo import models


class QueueJob(models.Model):
    """Model storing the jobs to be executed."""

    _inherit = "queue.job"

    def _message_post_on_failure(self):
        # subscribe the users now to avoid to subscribe them
        # at every job creation

        # @ol_upgrade(-8/0): We don't want to subscribe users or message/email them
        # domain = self._subscribe_users_domain()
        # base_users = self.env["res.users"].search(domain)
        # for record in self:
        # users = base_users | record.user_id
        # record.message_subscribe(partner_ids=users.mapped("partner_id").ids)
        # msg = record._message_failed_job()
        # if msg:
        # record.message_post(body=msg, subtype="queue_job.mt_job_failed")
        pass
