from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    osi_is_consu = fields.Boolean(string="Is Consumable")
