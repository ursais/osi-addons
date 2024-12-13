# Import Odoo libs
from odoo import fields, models


class PurchaseOrder(models.Model):
    """
    Adding fields to Purchase Order.
    """

    _inherit = "purchase.order"

    # COLUMNS ##########

    eco_id = fields.Many2one("mrp.eco", string="ECO")

    # END ##########
