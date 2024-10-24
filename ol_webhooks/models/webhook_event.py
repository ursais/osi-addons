# Import Python libs

# Import Odoo libs
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class WebhookEvent(models.Model):
    """
    Basic Webhook
    """

    _name = "webhook.event"
    _description = "Webhook Event"

    # COLUMNS #######
    name = fields.Char(string="Name")
    model_id = fields.Many2one(
        string="Model", comodel_name="ir.model", required=True, ondelete="cascade"
    )
    model_name = fields.Char(
        string="Model Name", related="model_id.model", required=True
    )
    operation = fields.Selection(
        string="Operation",
        selection=[
            ("create", "Create"),
            ("update", "Update"),
            ("delete", "Delete"),
        ],
        required=True,
    )
    is_custom = fields.Boolean(string="Is Custom Event", default=False)
    webhook_ids = fields.Many2many(
        string="Webhooks",
        comodel_name="webhook",
        relation="webhook_webhook_events",
        column1="webhook_event_id",
        column2="webhook_id",
    )
    # END COLUMNS ###

    def trigger(self, records, operation_override=False):
        """
        Trigger the webhooks related to the specific Webhook Event
        """
        self.ensure_one()
        # Get related enabled webhooks
        webhooks = self.webhook_ids.filtered(lambda w: w.enabled)

        if not webhooks:
            # Don't do anything if no related Webhook Event or enabled Webhooks exists
            return

        # Broadcast the events for the given webhooks
        webhooks.broadcast_all(self, records, operation_override=operation_override)
