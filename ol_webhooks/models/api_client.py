# Import Python libs
import uuid

# Import Odoo libs
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class WebhookClient(models.Model):
    """
    API Clients
    """

    _inherit = "api.client"

    # COLUMNS #######
    webhook_secret = fields.Char(
        string="Webhooks Secret",
        help=(
            "The Secret is used to validate the Webhook call for any service/app that listens for the"
            " requests."
        ),
    )
    webhook_url_hostname = fields.Char(
        string="Webhook Hostname",
        help="The base URL used for the Webhook URL. Ex.: `https://onlogic.com`",
    )
    webhook_url_path = fields.Char(
        string="Webhook Path",
        help="The path used for the Webhook URL. Ex.: `odoo-webhooks`",
    )
    webhook_url = fields.Char(
        string="Webhook Url",
        help="The full Webhook URL.",
        compute="_compute_url",
        store=True,
    )
    webhook_ids = fields.One2many(
        string="Webhooks", comodel_name="webhook", inverse_name="client_id"
    )
    run_webhooks_delayed = fields.Boolean(
        string="Run webhooks delayed",
        default=True,
        help="If enabled webhooks for the same record won't created queue_jobs if existing queue_jobs already exist.",
    )
    webhooks_enabled = fields.Boolean(
        string="Webhooks enabled", compute="_compute_webhooks_enabled"
    )
    # END COLUMNS ###

    def _compute_webhooks_enabled(self):
        """
        Compute the final URL based on the hostname and path
        """
        for client in self:
            client.webhooks_enabled = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_as_boolean("ol_webhooks.webhooks_enabled")
            )

    @api.depends("webhook_url_hostname", "webhook_url_path")
    def _compute_url(self):
        """
        Compute the final URL based on the hostname and path
        """
        for client in self:
            if not client.webhook_url_hostname or not client.webhook_url_path:
                client.webhook_url = False
            else:
                client.webhook_url = (
                    f"{client.webhook_url_hostname}/{client.webhook_url_path}"
                )
