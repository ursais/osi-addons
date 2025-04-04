# Import Odoo libs
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allowed_kit_component_cost = fields.Boolean(config_parameter='ol_mrp_sale_price_rollup.allowed_kit_component_cost',help="Enable for Allowed the Kit type Bill of martial into Product Template.",store=True)