# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    scrap_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )

    scrap_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Scrap Destination Location",
        domain="[('scrap_location', '=', True),"
        "('company_id', 'in', [company_id, False])]",
    )
