# Import Odoo libs
from odoo import fields, models, api


class ProductProduct(models.Model):
    """Add field to product.product to store Cost Base Pricing"""

    _inherit = "product.product"

    # COLUMNS ###

    last_purchase_line_ids = fields.One2many(
        comodel_name="purchase.order.line",
        inverse_name="product_id",
        domain=lambda self: [
            ("state", "in", ["purchase", "done"]),
            ("company_id", "in", self.env.companies.ids),
        ],
        string="Last Purchase Order Lines",
        store=True,
    )
    last_purchase_price = fields.Float(
        compute="_compute_last_purchase_line_id_info",
        store=True,
        company_dependent=True,
    )
    cost_base_pricing = fields.Float()

    # END #######

    @api.depends("last_purchase_line_id")
    def _compute_last_purchase_line_id_info(self):
        """Override method for updating last purchase info only when the
        vendor is from a non-internal company"""
        for item in self:
            if (
                item.last_purchase_line_id.partner_id.company_id.id
                not in self.env.companies.ids
            ):
                item.last_purchase_price = item.last_purchase_line_id.price_unit
                item.last_purchase_date = item.last_purchase_line_id.date_order
                item.last_purchase_supplier_id = item.last_purchase_line_id.partner_id
                item.last_purchase_currency_id = item.last_purchase_line_id.currency_id
