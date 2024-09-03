# Import Odoo libs
from odoo import fields, models


class SaleOrderTemplate(models.Model):
    """
    Add new fields to Sale Order Template
    """

    _inherit = "sale.order.template"

    # COLUMNS #####

    partner_id = fields.Many2one(
        "res.partner",
        help="""Enter a Partner if this quote is specific to the Partner,
        leave blank if this template can be used for all sale orders.""",
    )

    # END #########
