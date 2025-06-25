# Import Odoo libs
from odoo import fields, models


class ResCompany(models.Model):
    """Add delivery related data to the company record"""

    _inherit = "res.company"

    # COLUMNS #####
    minimum_volume = fields.Float(string="Minimum Volume", digits="OnLogic Volume", default=0.00001)
    
    use_delivery_uplift = fields.Boolean(
        string='Enable Shipping Uplift',
        help=(
            'If Uplift is enabled the Weight and Volume are increased'
            'by a percentage defined by the `Uplift percent`'
        ),
        default=True,
    )

    delivery_weight_uplift = fields.Float(string="Weight Uplift Percent", default=10)

    delivery_dimension_uplift = fields.Float(string="Volume Uplift Percent", default=10)
    # END #########
