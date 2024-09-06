# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Override sale_order_template_id changing domain.
    """

    _inherit = "sale.order"

    # COLUMNS #####

    sale_order_template_id = fields.Many2one(
        domain="[('partner_id', 'in', [False, partner_id]), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    # END #########
