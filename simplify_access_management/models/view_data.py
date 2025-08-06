from odoo import fields, models, api, _

class view_data(models.Model):
    _name = 'view.data'
    _description = "View Data"

    name = fields.Char('Name')
    techname = fields.Char('Tech Name')


    