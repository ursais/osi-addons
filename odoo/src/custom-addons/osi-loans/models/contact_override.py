from odoo import models, api, fields



class ContactOverride(models.Model):
    _inherit = 'res.partner'
    employment_status = fields.Char(string="Employment Status")


