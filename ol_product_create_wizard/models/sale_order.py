# Import Odoo libs
from odoo import _, models


class SaleOrder(models.Model):
    """Add new wizard to sale order"""

    _inherit = "sale.order"

    # METHODS #########

    def open_create_product(self):
        # Prepare the action to open the "Add Components" wizard
        return {
            "name": _("Create Product"),
            "type": "ir.actions.act_window",
            "res_model": "product.create.wizard",
            "view_mode": "form",
            "target": "new",
        }

    # END #########
