from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    account_manager_id = fields.Many2one("res.users", string="Account Manager")
