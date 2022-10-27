from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_user_ids = fields.Many2many("res.users", string="Additional Salesperson")
