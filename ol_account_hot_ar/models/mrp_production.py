# Import Odoo Libs
from odoo import fields, models


class MrpProduction(models.Model):
    """Add related hot_ar field to trigger exception checks."""

    _inherit = "mrp.production"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        related="sale_order_id.partner_invoice_id.commercial_partner_id.hot_ar",
        store=True,
        help="""Customer hot AR status""",
    )

    # END #########
