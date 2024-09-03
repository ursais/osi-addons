# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order
    """

    _inherit = "sale.order"

    # COLUMNS #####

    sale_order_template_id = fields.Many2one(
        comodel_name="sale.order.template",
        string="Quotation Template",
        compute="_compute_sale_order_template_id",
        store=True,
        readonly=False,
        check_company=True,
        precompute=True,
        domain="[('partner_id', 'in', [False, partner_id]), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    # END #########
