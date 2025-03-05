# Import Odoo libs
from odoo import api, models


class SaleOrder(models.Model):
    """Inherit sale order for CRM tag management."""

    _inherit = "sale.order"

    # METHODS #####

    def _update_tags_from_opportunity(self):
        # Append CRM Stage Tags into Sale Order
        self.ensure_one()
        if self.opportunity_id and self.opportunity_id.stage_id:
            crm_tags = self.opportunity_id.stage_id.tag_ids.ids
            # Append new tags without removing existing ones
            self.tag_ids = [(4, tag_id) for tag_id in crm_tags]

    def _remove_tags_from_previous_opportunity(self, previous_opportunity):
        # Remove tags from the previous opportunity's stage
        if previous_opportunity and previous_opportunity.stage_id:
            previous_tags = previous_opportunity.stage_id.tag_ids.ids
            self.tag_ids = [(3, tag_id) for tag_id in previous_tags]

    @api.model
    def create(self, vals):
        # Append CRM Stage Tags into Sale Order during creation
        sale_order = super().create(vals)
        if sale_order.opportunity_id:
            sale_order._update_tags_from_opportunity()
        return sale_order

    @api.onchange("opportunity_id")
    def _onchange_opportunity_id(self):
        # Append CRM Stage Tags into Sale Order during opportunity updates
        if self.opportunity_id:
            previous_opportunity = self._origin.opportunity_id
            self._remove_tags_from_previous_opportunity(previous_opportunity)
            if not previous_opportunity:
                #It will execute When Sale Order is not saved from opportunity.
                self.tag_ids = False
            self._update_tags_from_opportunity()

    # END ##########
