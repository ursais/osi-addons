# Import Python Libs
from datetime import datetime, timedelta
import logging

# Import Odoo Libs
from odoo import models, fields
from odoo.addons.ol_base.fields import fields as ol_fields
from odoo.addons.queue_job.job import STATES

_logger = logging.getLogger(__name__)


class GraphQLQueue(models.Model):
    """
    The model to keep track of incoming graphql mutations
    """

    _name = "graphql.queue"
    _description = "GraphQL Queue Object"

    # COLUMNS ###
    name = fields.Char(string="Name")
    operation = fields.Selection(
        selection=[
            ("create", "Create"),
            ("update", "Update"),
            ("delete", "Delete"),
        ],
        string="Operation",
        index=True,
    )
    record_uuid = ol_fields.Uuid(
        string="Odoo Record UUID",
        index=True,
    )
    transaction_id = fields.Char(
        string="Transaction ID",
        index=True,
    )
    message_source = fields.Char(
        string="Message Source",
        index=True,
    )
    odoo_class = fields.Char(
        string="Odoo Class",
        index=True,
    )
    publish_time = ol_fields.Timestamp(
        string="Message Publish Time",
        help="Timestamp when this message was originally received by Google Pub/Sub",
        index=True,
    )
    values = fields.Text(string="Values", readonly=True)
    queue_job_id = fields.Many2one(
        comodel_name="queue.job", string="Queue Job", compute="_compute_queue_job_id"
    )
    state = fields.Selection(selection=STATES, compute="_compute_queue_job_id")
    exc_message = fields.Char(
        string="Exception Message", compute="_compute_queue_job_id"
    )
    exc_info = fields.Text(string="Exception Info", compute="_compute_queue_job_id")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    # END #######

    def _compute_queue_job_id(self):
        queue_job_data = self.queue_job_data()
        for queue in self:
            queue_job = queue_job_data.get(queue.id, self.env["queue.job"])
            queue.queue_job_id = queue_job
            queue.state = queue_job.state
            queue.exc_message = queue_job.exc_message
            queue.exc_info = queue_job.exc_info

    def queue_job_data(self):
        """
        Get related queue.job
        """

        # Handle NewIds
        graphql_queue_ids = [
            x._origin.id if isinstance(x.id, models.NewId) else x.id for x in self
        ]

        if not graphql_queue_ids:
            return self.env["queue.job"]

        query = """
            SELECT
                qj.id AS queue_job_id,
                qj.graphql_queue_id AS graphql_queue_id
            FROM
                queue_job qj
            WHERE
            qj.graphql_queue_id IN %(graphql_queue_ids)s
        """

        query_args = {"graphql_queue_ids": tuple(graphql_queue_ids)}
        self.env.cr.execute(query, query_args)
        results = self.env.cr.dictfetchall()
        # SUDO is required here since the queue.job record values are accessed in subsequent methods and, since some may exist in other companies, this will throw a multi company error without sudo
        return {
            x["graphql_queue_id"]: self.env["queue.job"]
            .sudo()
            .browse(x["queue_job_id"])
            for x in results
        }

    def open_queue_job(self):
        """
        Open the form view of the related queue.job
        """
        return {
            "type": "ir.actions.act_window",
            "res_model": "queue.job",
            "name": self.queue_job_id.name,
            "target": "current",
            "view_mode": "form",
            "view_id": self.env.ref("queue_job.view_queue_job_form").id,
            "res_id": self.queue_job_id.id,
        }

    def autovacuum(self):
        """
        Clean up the 'graphql.queue' table
        Delete all queue items that are older than 30 days
        Called from a cron.
        """

        _logger.info("Running `graphql.queue` autovacuum.")

        deadline = datetime.now() - timedelta(days=int(30))

        # We always want to keep the last entry even if it's old
        # We find their IDs and exclude them in the search below
        query = """
            SELECT DISTINCT ON (record_uuid) record_uuid,
                gq.id
            FROM graphql_queue gq
            ORDER BY gq.record_uuid, gq.publish_time DESC
            """
        self.env.cr.execute(query)
        latest_record_ids = [row["id"] for row in self.env.cr.dictfetchall()]
        while True:
            records = self.sudo().search(
                [("publish_time", "<=", deadline), ("id", "not in", latest_record_ids)],
                limit=1000,
            )
            if records:
                records.unlink()
                self.env.cr.commit()
            else:
                break
        return True
