from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vw_product_ref = fields.Char(string="VW Product Reference")
