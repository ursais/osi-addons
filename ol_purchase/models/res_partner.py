# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """
    Adding fields to Partner.
    """

    _inherit = "res.partner"

    # COLUMNS ##########

    approved_vendor = fields.Boolean(
        default=False,
        help="Indicates if the vendor is approved for purchasing."
    )

    # END ##########
