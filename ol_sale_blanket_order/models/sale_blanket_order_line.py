# Import Odoo libs
from odoo import api, fields, models


class SaleBlanketOrderLine(models.Model):
    """
    Add new fields to Sale blanket Order Line
    """

    _inherit = "sale.blanket.order.line"

    # COLUMNS #####

    customer_lead = fields.Float(compute="_compute_customer_lead")

    # END #########

    # METHODS #########

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay

    # END ######
