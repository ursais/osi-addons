# Import Odoo libs
from odoo import fields, api, models


class StockScrap(models.Model):
    """Inherit scrap to override set location functionality."""

    _inherit = "stock.scrap"

    # COLUMNS #####

    scrap_location_id = fields.Many2one(
        "stock.location",
        "Scrap Location",
        compute="_compute_scrap_location_id",
        store=True,
        required=True,
        domain="[('scrap_location', '=', True)]",
        check_company=True,
        readonly=False,
    )

    # END #########
    # METHODS #####

    @api.depends("company_id", "reason_code_id")
    def _compute_scrap_location_id(self):
        """OVERRIDE to allow manual setting of location_id
        and bypass automatic calculation."""
        for scrap in self:
            # Compute the location if it's not manually set by the user
            if not scrap.scrap_location_id:
                scrap.scrap_location_id = scrap.reason_code_id.location_id.id

    # END #########
