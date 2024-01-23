# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class Commission(models.Model):
    _inherit = "commission"

    commission_type = fields.Selection(selection_add=[('amount', 'Amount')], ondelete={'amount': 'cascade'})
    amount = fields.Float()
