# Import Odoo libs
from odoo import fields, models, api


class QueueJob(models.Model):
    _inherit = "queue.job"

    transaction_id = fields.Char(
        string="Transaction ID",
        index=True,
    )

    graphql_queue_id = fields.Many2one(
        comodel_name="graphql.queue", string="GraphQL Queue", index=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        If the `graphql_queue_id` id was present in the context
        link the current `queue.job` to this GQL Event.
        This helps us to link queue jobs to specific events
        """

        if any(
            x for x in ["graphql_queue_id", "transaction_id"] if x in self.env.context
        ):
            for values in vals_list:
                values["transaction_id"] = self.env.context.get("transaction_id", False)
                values["graphql_queue_id"] = self.env.context.get(
                    "graphql_queue_id", False
                )
        return super().create(vals_list)
