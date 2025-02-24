# Import Odoo libs
from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _update_tags_from_opportunity(self):
        # Append CRM Stage into Sale Order
        self.ensure_one()
        if self.opportunity_id and self.opportunity_id.stage_id:
            55/0
            crm_tags = self.opportunity_id.stage_id.tag_ids.ids
            self.tag_ids = [(6, 0, crm_tags)]

    @api.model
    def create(self, vals):
        sale_order = super().create(vals)
        if sale_order.opportunity_id:
            sale_order._update_tags_from_opportunity()
        return sale_order

    @api.onchange("opportunity_id")
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            self._update_tags_from_opportunity()
