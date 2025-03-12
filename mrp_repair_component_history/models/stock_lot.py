# Import Odoo libs
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    # COLUMNS ###

    component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Component History",
    )
    show_invisible = fields.Boolean(
        string="Show All History",
        default=True,
        help="By default, only 'current' components are shown so if a component was removed the removed line will show and the original is hidden. Click to see the full history.",
    )
    visible_component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Visible Component History",
        compute="_compute_visible_component_history_ids",
    )

    # METHODS #######

    def toggle_show_invisible(self):
        """Toggles the visibility of invisible component history records."""
        self.show_invisible = not self.show_invisible

    @api.depends("show_invisible", "component_history_ids")
    def _compute_visible_component_history_ids(self):
        for lot in self:
            if lot.show_invisible:
                lot.visible_component_history_ids = lot.component_history_ids
            else:
                lot.visible_component_history_ids = lot.component_history_ids.filtered(
                    lambda r: not r.invisible
                )

    # END #######
