# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    amount_include_tax = fields.Boolean(
        "Include Taxes in Amount", default=False, copy=False
    )
