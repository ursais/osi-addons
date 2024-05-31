from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    audi_business_unit = fields.Char(string="Business Unit")
    audi_applicant_email = fields.Char(string="Applicant email")

