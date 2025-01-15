# Import Odoo libs
from odoo import fields, models, api


class WebhookSettings(models.TransientModel):
    """
    Handles default Webhook Search settings.
    """

    _inherit = "res.config.settings"

    # COLUMNS #######
    webhooks_enabled = fields.Boolean(
        string="Enabled",
        help="Main switch to enable or disable Odoo Webhooks",
        config_parameter="ol_webhooks.webhooks_enabled",
    )

    # END #########

    @api.model
    def create(self, values):
        # Saving a res_config even without changing any values will trigger the write of all
        # related values on res_company. This in return could affect a lot of other records like
        # `sale.order`, `account.move`, `product.template` in these instances we don't want to
        # trigger related webhooks.
        return super(WebhookSettings, self.with_context(skip_webhooks=True)).create(
            values
        )
