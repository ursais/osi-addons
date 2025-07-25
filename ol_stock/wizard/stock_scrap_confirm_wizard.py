# Import Odoo libs
from odoo import models


class StockScrapConfirmWizard(models.TransientModel):
    """Confirmation wizard."""

    _name = "stock.scrap.confirm.wizard"
    _description = "Confirm Scrap of Reserved Products"

    # METHODS #####

    def action_confirm(self):
        scrap_id = self.env["stock.scrap"].browse(self._context.get("active_id"))
        return scrap_id.do_scrap()

    # END #########
