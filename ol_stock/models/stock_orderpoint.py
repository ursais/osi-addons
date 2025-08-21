# Import Odoo Libs
from odoo import fields, models


class StockOrderpoint(models.Model):
    """Inherit Order Point to add overflow bool and cron."""

    _inherit = "stock.warehouse.orderpoint"

    # COLUMNS #####

    is_overflow = fields.Boolean(string="Is Overflow")

    # END #########
    # METHODS ######

    def _cron_run_overflow_replenishments(self):
        domain = [("is_overflow", "!=", False), ("active", "=", True)]
        orderpoints = self.search(domain)
        if orderpoints:
            orderpoints.action_replenish()

    # END ##########
