# Import Python libs

# Import Odoo libs
from odoo import models


class Partner(models.Model):
    """
    Add webhook compatibility to Partners
    """

    _name = "res.partner"
    _inherit = ["res.partner", "webhook.mixin"]

    def _create_filter(self, values):
        """
        Any filtering logic that needs to happen before we want to trigger webhooks
        """

        # Records filtered by the mixin
        partner_ids = super()._create_filter(values)

        # Filter anything that is not a Company or does not have a CRM Customer
        return partner_ids.webhook_filter()

    def _update_filter(self, values):
        """
        Any filtering logic that needs to happen before we want to trigger webhooks
        """

        # Records filtered by the mixin
        partner_ids = super()._update_filter(values)

        # Filter anything that is not a Company or does not have a CRM Customer
        return partner_ids.webhook_filter()

    def _delete_filter(self):
        """
        Any filtering logic that needs to happen before we want to trigger webhooks
        """

        # Records filtered by the mixin
        partner_ids = super()._delete_filter()

        # Filter anything that is not a Company or does not have a CRM Customer
        return partner_ids.webhook_filter()

    def webhook_filter(self):
        """
        Filter anything that is not a Company or does not have a CRM Customer
        TODO: This should be changed now that we don't have the res.customer solution
        """
        return self.filtered(lambda partner_id: partner_id or partner_id.is_company)

    def trigger_custom_events(self, partner_ids, values, operation):
        """
        Trigger additional webhooks adjacent to the partner webhooks
        """
        # Trigger company webhooks and return all partners that are not companies
        partner_ids = self.trigger_company_webhook_event(partner_ids, values, operation)
        # Trigger sale order webooks. We do not modify partners, so no need to redefine them
        self.trigger_sale_order_webhook_event(partner_ids, values, operation)
        return partner_ids, values

    def trigger_company_webhook_event(self, partner_ids, values, operation):
        """
        Trigger a different events for Companies than for other `res.partner` records
        Only pass on non Company records
        """

        # Filter the records based on any record/business logic
        companies = partner_ids.filtered(lambda partner_id: partner_id.is_company)

        # Find the specific `webhook.even` XML record
        webhook_event = self.env.ref(f"ol_webhooks.company_{operation}")

        if companies and webhook_event:
            # If the filter returned any records and we found the `webhook.event`
            webhook_event.trigger(records=companies, operation_override=operation)

        # Decide if we want to allow all records to be passed on, or remove some
        non_companies = partner_ids - companies
        return non_companies

    def trigger_sale_order_webhook_event(self, partner_ids, values, operation):
        """
        Trigger sale order webhooks if the partner was edited using the external link button
        """
        # This context variable is only set from a specific view path to connect an address to a sale order
        sale_order = self.env["sale.order"].browse(
            self.env.context.get("sale_order_invoice_address_webhook_trigger", False)
        )
        if sale_order.exists():
            # Trigger a webhook for the sale order
            sale_order.trigger_webhook()

    def trigger_webhooks_for_related(self):
        # Get all child and parent records of the given invoices partner
        # We don't care if this given partner is a company or a CRM Customer
        # as it's parent child records could be
        related_partners = self.get_direct_family_tree()
        related_partners.trigger_webhook()
