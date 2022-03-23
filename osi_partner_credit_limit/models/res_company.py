from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    credit_limit_amount = fields.Float("Credit Limit Amount")
