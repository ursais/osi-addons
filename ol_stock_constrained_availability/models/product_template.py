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

    def set_is_constrained(self):
        active_ids = self.browse(self._context.get("active_ids"))
        if 'is_constrained' in self._context:
            active_ids.write({"is_constrained":self._context.get("is_constrained")})
    # END #########
