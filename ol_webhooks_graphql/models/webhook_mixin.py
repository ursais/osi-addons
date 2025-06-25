# Import Python libs

# Import Odoo libs
from odoo import models
from odoo.osv import expression


class WebhookMixin(models.AbstractModel):
    _inherit = "webhook.mixin"

    def _create_filter(self, values):

        empty_recordset = self.env[self._name]
        if self.is_graphql_call():
            return empty_recordset

        return super()._create_filter(values)

    def base_filter(self, values):

        empty_recordset = self.env[self._name]
        if self.is_graphql_call():
            return empty_recordset

        return super().base_filter(values)

    def is_graphql_call(self):
        """
        Don't trigger related webhooks if it was triggered from an incoming GraphQL message
        """

        if not self.env.context.get(
            "webhook_skip_graphql_incoming_check"
        ) and self.env.context.get("graphql_incoming_message", False):
            return True
        return False

    def _get_graphql_updated_since_domain(self, domain, date_limit):
        """
        For records that implement Webhooks we want to make sure the `updated_since` GraphQL Query
        takes webhooks calls into consideration.
        """
        base_domain = [("graphql_update_date", ">=", date_limit)]
        common_domain = expression.OR(
            [[("webhook_broadcast_date", ">=", date_limit)], base_domain]
        )

        domain = expression.AND([common_domain, domain])
        return domain

    def get_record_dates_data(self):
        """
        Add the `webhook_broadcast_date` to the GQL dates data
        """
        res = super().get_record_dates_data()
        res.update({"webhook_broadcast_date": self.webhook_broadcast_date})
        return res
