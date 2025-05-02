# Import Odoo Libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit the Object for Field adding."""

    _inherit = "product.template"

    # FIELDS #####

    is_constrained = fields.Boolean(
        string="Is Constrained?",
        help="Use sale order confirmation date instead of scheduled date for availability forecasting.",
        groups="stock.group_stock_user",
        company_dependent=True,
    )
    # END #########
