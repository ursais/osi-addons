# Import Odoo libs
from odoo import models


class ResPartner(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "res.partner"
    _inherit = ["res.partner", "graphql.mixin"]

    def _post_graphql_create_actions(self, **kwargs):
        """
        After we create a record via GraphQL we want to trigger an update webhook.
        The allows us to feed-back data that was added by odoo after creation
        """

        if not self.is_graphql_placeholder:
            # Only trigger a webhook if this is not a GraphQL placeholder record

            # List of fields we want to send in this webhook
            fields_to_sync = [
                "create_id",
                "credit_limit",
                "customer_rank",
                "late_payment",
                "odoo_url",
                "supplier_rank",
                "tax_exempt",
                "tax_exemption_code",
                "tax_exemption_number",
                "update_id",
                "uuid",
                "vat",
            ]
            self.with_context(
                force_webhook_trigger=True,
                webhook_skip_graphql_incoming_check=True,
                fields_to_sync=fields_to_sync,
            )._event_update({})
        return super()._post_graphql_create_actions(**kwargs)
