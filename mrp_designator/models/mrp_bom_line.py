# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    designator = fields.Char()
