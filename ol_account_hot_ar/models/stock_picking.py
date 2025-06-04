# Import Odoo Libs
from odoo import fields, models


class StockPicking(models.Model):
    """Add related hot_ar field to trigger exception checks."""

    _inherit = "stock.picking"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        related="sale_id.partner_invoice_id.commercial_partner_id.hot_ar",
        store=True,
        help="""Customer hot AR status""",
    )

    # END #########
