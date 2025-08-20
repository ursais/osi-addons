from odoo import fields, models, api, _


class action_data(models.Model):
    _name = 'action.data'
    _description = "Action Data"

    name = fields.Char('Name')
    action_id = fields.Many2one('ir.actions.actions', 'Action')
