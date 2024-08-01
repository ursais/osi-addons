# Import Odoo libs
from odoo import fields, models


class PlmEcoStage(models.Model):
    """
    Add field to PLM ECO Stage
    """

    _inherit = "mrp.eco.stage"

    # COLUMNS #####

    cancel_stage = fields.Boolean(
        string="Cancel Stage",
        help="When the Cancel button is pressed, the ECO will move to this stage"
        " and the product's stage will be reset to it's original stage.",
    )

    # END #########
