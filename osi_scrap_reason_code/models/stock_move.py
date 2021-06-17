# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    reason_code_id = fields.Many2one("reason.code", string="Reason code")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    scrap_location = fields.Boolean(
        related="location_dest_id.scrap_location",
        string="Scrap Location flag",
        store=True)
