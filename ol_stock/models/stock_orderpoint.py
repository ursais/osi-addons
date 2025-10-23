# Import Odoo Libs
from odoo import fields, models


class StockOrderpoint(models.Model):
    """Inherit Order Point to add overflow bool and cron."""

    _inherit = "stock.warehouse.orderpoint"

    # COLUMNS #####

    is_overflow = fields.Boolean(string="Is Overflow")

    # END #########
    # METHODS ######

    def _cron_run_overflow_replenishments(self, company_id=None):
        """Run overflow replenishments for a specific company if provided."""
        companies = (
            self.env["res.company"].browse(company_id)
            if company_id
            else self.env["res.company"].search([])
        )
        for company in companies:
            orderpoints = self.with_company(company).search(
                [
                    ("is_overflow", "!=", False),
                    ("active", "=", True),
                ]
            )
            if orderpoints:
                orderpoints.action_replenish()

    # END ##########
