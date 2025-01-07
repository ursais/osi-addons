from odoo import api, fields, models


class ProductProfile(models.Model):
    _inherit = "product.profile"

    def _get_default_category_id(self):
        return self.env.ref('product.product_category_all')

    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        change_default=True,
        default=_get_default_category_id
    )
    uom_id = fields.Many2one(
        "uom.uom",
        "Unit of Measure",
        default=_get_default_uom_id
    )
    uom_po_id = fields.Many2one(
        "uom.uom",
        "Purchase UoM",
    )
    route_ids = fields.Many2many(
        "stock.route",
        "stock_route_product_profile",
        "product_profile_id",
        "route_id",
        "Routes",
        domain=[('product_selectable', '=', True)],
        depends_context=['company', 'allowed_companies'],
    )
    invoice_policy = fields.Selection(
        selection=[
            ('order', "Ordered quantities"),
            ('delivery', "Delivered quantities"),
        ],
        string="Invoicing Policy",
        help="Ordered Quantity: Invoice quantities ordered by the customer.\n"
             "Delivered Quantity: Invoice quantities delivered to the customer.")
