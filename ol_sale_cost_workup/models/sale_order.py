# Import Odoo libs
from odoo import models
import base64
from datetime import datetime


class SaleOrder(models.Model):
    """
    BOM Lines and Option Lines related functionality
    """

    _inherit = "sale.order"

    # METHODS #######

    def getBOMLines(self, sol=None):
        return (
            self.env["mrp.bom"]
            .search([("product_id", "=", sol.product_id.id)], limit=1)
            .bom_line_ids
        )

    def getOptionLines(self, sol=None):
        return self.env["sale.order.option"].search(
            [("product_id", "=", sol.product_id.id), ("order_id", "=", sol.order_id.id)]
        )

    def create_cost_workup_report(self):
        """Render the Cost Workup Report and attach it to the SO in `self`."""
        report = self.env["ir.actions.report"]._render_qweb_pdf(
            "ol_sale_cost_workup.report_costworkup", self.id
        )

        # Get today's date in the format YYYY-MM-DD
        today_str = datetime.today().strftime("%Y-%m-%d")
        # Construct the filename using the SO name and today's date
        filename = "Cost_Workup_%s_%s.pdf" % (self.name, today_str)

        self.env["ir.attachment"].create(
            {
                "name": filename,
                "type": "binary",
                "datas": base64.b64encode(report[0]),
                "res_model": "sale.order",
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )

    def action_quotation_send(self):
        """Create Cost Workup Report on 'Send Email' button."""
        res = super().action_quotation_send()
        self.create_cost_workup_report()
        return res

    def action_lock(self):
        """Extend action_done to generate and attach the Cost Workup report
        when SO gets locked. Also triggers on confirmation."""
        res = super().action_lock()

        # Generate and attach the Cost Workup report after the SO is locked
        self.create_cost_workup_report()

        return res

    # END #########
