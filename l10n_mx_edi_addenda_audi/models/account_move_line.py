from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    audi_product_ref = fields.Char(string="Audi Product Reference")
