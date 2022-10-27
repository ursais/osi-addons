from odoo import fields, models


class CRMLead(models.Model):
    _inherit = "crm.lead"

    sale_user_ids = fields.Many2many("res.users", string="Additional Salesperson")
