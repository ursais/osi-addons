from odoo import models,fields,api,_

class ir_module_module(models.Model):
    _inherit = "ir.module.module"


    def button_immediate_uninstall(self):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        if self.name == 'simplify_access_management':
            value = config_parameter_obj.search([('key','=','uninstall_simplify_access_management')],limit=1)
            if value:
                value.value = 'True'
            else:
                config_parameter_obj.create({'key':'uninstall_simplify_access_management','value':'True'})
            
        res = super(ir_module_module,self).button_immediate_uninstall()
        config_parameter_obj.search([('key','=','uninstall_simplify_access_management')],limit=1).unlink()

        return res

