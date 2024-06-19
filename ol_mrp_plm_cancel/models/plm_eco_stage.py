# Import Odoo libs
from odoo import fields, models, api


class PlmEcoStage(models.Model):
    """
    Add field to PLM ECO Stage
    """
    _inherit = "mrp.eco.stage"

    # COLUMNS #####
    cancel_stage = fields.Boolean(
        string="Cancel Stage",
    )
    # END #########

    @api.onchange("cancel_stage")
    def onchange_cancel_stage(self):
        if self.cancel_stage:
            self.state = 'cancel'
