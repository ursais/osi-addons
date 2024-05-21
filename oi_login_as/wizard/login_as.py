'''
Created on May 13, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api
from odoo.exceptions import AccessError

class LoginAs(models.TransientModel):
    _name = 'login.as'
    _description = _name
    
    group_id = fields.Many2one('res.groups')
    user_id = fields.Many2one('res.users', required = True, ondelete = 'cascade')
    
    group_ids = fields.Many2many('res.groups', compute = '_calc_group_ids', string = 'User Groups')
    company_id = fields.Many2one(related='user_id.company_id', readonly=True)
    company_ids = fields.Many2many(related='user_id.company_ids', readonly=True)
    
    def switch_to_user(self):
        if not self.env.user._is_system():
            raise AccessError('System User Only')
        return {
            'type' : 'ir.actions.act_url',
            'url' : '/web/login_as/%d' % self.user_id.id,
            'target' : 'self'
            }
    
    @api.onchange('group_id')
    def _onchange_group_id(self):
        if self.group_id and self.group_id not in self.user_id.groups_id:
            self.user_id = False
    
    @api.depends('user_id')
    def _calc_group_ids(self):
        for record in self:
            record.group_ids = record.user_id.groups_id.filtered(lambda group : group.category_id.visible).sorted('full_name')