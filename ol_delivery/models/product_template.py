from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Delivery related additions to the Product Template Model
    """

    _inherit = 'product.template'

    # COLUMNS #####
    shipping_buffer = fields.Integer(
        string="Shipping Buffer",
        help="The number of buffer days before carrier pickup",
        company_dependent=True,
    )
    lithium_shipping_hazard = fields.Boolean(
        string='Lithium Shipping Hazard',
        help='Products that have a risk of fire must be declared when shipped',
    )
    # END COLUMNS #