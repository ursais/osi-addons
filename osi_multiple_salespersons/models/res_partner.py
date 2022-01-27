from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_user_ids = fields.Many2many("res.users", string="Additional Salesperson")
