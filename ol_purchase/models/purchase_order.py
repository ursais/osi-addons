# Import Odoo libs
from odoo import fields, models


class PurchaseOrder(models.Model):
    """
    Adding fields to Purchase Order.
    """

    _inherit = "purchase.order"

    # COLUMNS ##########

    approved_vendor = fields.Boolean(
        related="partner_id.approved_vendor",
        help="Indicates if the vendor is approved for purchasing.",
    )

    # END ##########
