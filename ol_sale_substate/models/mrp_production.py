# Import Odoo libs
from odoo import models


class MrpProduction(models.Model):
    """Add method to compute the sale substate change for production."""

    _inherit = "mrp.production"

    # METHODS #####

    def _update_related_sale_substates(self):
        """Trigger sale orders substate update method to update their substates."""
        sale_order = self.sale_order_id
        if sale_order:
            sale_order.update_substate()

    def action_confirm(self):
        """Trigger a substate check if confirm is pressed"""
        res = super().action_confirm()
        self._update_related_sale_substates()
        return res

    def button_plan(self):
        """Trigger a substate check if planned button is pressed"""
        res = super().button_plan()
        self._update_related_sale_substates()
        return res

    def button_unplan(self):
        """Trigger a substate check if unplan button is pressed"""
        res = super().button_unplan()
        self._update_related_sale_substates()
        return res

    def button_mark_done(self):
        """Trigger a substate check if produce is pressed"""
        res = super().button_mark_done()
        self._update_related_sale_substates()
        return res

    def write(self, vals):
        """
        Trigger a substate check if the MO state changes.
        Structured so other fields could be added later is needed.
        """
        res = super().write(vals)
        if any(field in vals for field in ("state")):
            self._update_related_sale_substates()
        return res

    # END #####
