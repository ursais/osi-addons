from odoo import models


class base_module_uninstall(models.TransientModel):
    _inherit = "base.module.uninstall"
   
    def action_uninstall(self):
        if 'simplify_access_management' in self.module_ids.mapped('name'):
            param_obj = self.env['ir.config_parameter'].sudo()
            value = param_obj.search([('key','=','uninstall_check')],limit=1)
            if value:
                value.value = "True"
            else:
                param_obj.create({'key':'uninstall_check','value':'True'})
            self._cr.commit()
        return super(base_module_uninstall, self).action_uninstall()
