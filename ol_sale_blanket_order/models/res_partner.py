from odoo import fields, models


class ResPartner(models.Model):
    """
    Add new fields to Res partner
    """

    _inherit = "res.partner"

    sale_blanket_order_ids = fields.One2many(
        "sale.blanket.order", "partner_id", "Sales Blanket Order"
    )
