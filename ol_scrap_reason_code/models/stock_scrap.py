# Import Odoo libs
from odoo import fields, api, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    scrap_location_id = fields.Many2one(
        "stock.location",
        "Scrap Location",
        compute="_compute_scrap_location_id",
        store=True,
        required=True,
        precompute=True,
        domain="[('scrap_location', '=', True)]",
        check_company=True,
        readonly=False,
    )

    @api.depends("company_id", "reason_code_id")
    def _compute_scrap_location_id(self):
        """OVERRIDE to bypass the OCA/scrap_reason_code module functionality"""
        for scrap in self:
            scrap.scrap_location_id = scrap.reason_code_id.location_id.id

    # END #########
