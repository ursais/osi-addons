# Import Odoo libs
from odoo import fields, models


class PLMECOStage(models.Model):
    """
    Add field to PLM ECO Stage
    """

    _inherit = "mrp.eco.stage"

    # COLUMNS #####

    product_state_id = fields.Many2one(
        comodel_name="product.state",
        string="Product State",
        help="Select a state for this product",
    )
    allow_bom_edits = fields.Boolean(string="Allow Modifications")

    # END #########
