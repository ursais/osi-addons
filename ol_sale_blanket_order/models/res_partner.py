# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """
    Add new fields to Res partner
    """

    _inherit = "res.partner"

    # COLUMNS #####

    sale_blanket_order_ids = fields.One2many(
        comodel_name="sale.blanket.order",
        inverse_name="partner_id",
        string="Sales Blanket Order",
    )

    # END #########
