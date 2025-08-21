from odoo import api, fields, models, tools


class ir_actions_actions(models.Model):
    _inherit = 'ir.actions.actions'


    @api.model_create_multi
    def create(self, vals_list):
        res = super(ir_actions_actions, self).create(vals_list)
        action_data_obj = self.env['action.data'].sudo()
        for record in res:
            action_data_obj.create({'name':record.name,'action_id':record.id})
        return res

    def unlink(self):
        action_data_obj = self.env['action.data'].sudo()
        for record in self:
            action_data_obj.search([('action_id','=',record.id)]).unlink()
        return super(ir_actions_actions, self).unlink()
