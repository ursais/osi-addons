# Import Odoo Libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Add related hot_ar field to trigger exception checks."""

    _inherit = "sale.order"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        related="partner_invoice_id.commercial_partner_id.hot_ar",
        store=True,
        help="""Customer hot AR status""",
    )

    # END #########
