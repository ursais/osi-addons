# Import Odoo libs
from odoo import models


class SaleBooking(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = 'sale.booking'
    _inherit = ['sale.booking', 'webhook.mixin']

    def is_graphql_call(self):
        """
        By default, we don't trigger related webhooks for any actions that were triggered from an incoming GraphQL message.

        However, we do want to send messages for Sale Bookings that are created from incoming website orders via GraphQL.
        """

        # List of functions that should force trigger a webhook at the end
        # `graphql_incoming_message` is set in `persist_mutation_data`
        trigger_list = ['create']

        webhook_skip_graphql_incoming_check = (
            self.env.context.get('graphql_incoming_message', False) in trigger_list
        )

        return super(
            SaleBooking,
            self.with_context(webhook_skip_graphql_incoming_check=webhook_skip_graphql_incoming_check),
        ).is_graphql_call()
