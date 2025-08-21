from odoo import fields, models, api, SUPERUSER_ID,_
from odoo.exceptions import UserError, AccessDenied
from .query_prepare import search_data
import logging
_logger = logging.getLogger(__name__)

class res_users(models.Model):
    _inherit = 'res.users'

    access_management_ids = fields.Many2many('access.management', 'access_management_users_rel_ah', 'user_id', 'access_management_id', 'Access Pack')

    def write(self, vals):
        res = super(res_users, self).write(vals)
        for user in self:
            for access in user.sudo().access_management_ids:
                if user.env.company in access.company_ids and access.readonly:
                    if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user can not be set as a read-only..!'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(res_users, self).create(vals_list)
        for record in self:
            for access in record.sudo().access_management_ids:    
                if self.env.company in access.company_ids and access.readonly:
                    if record.has_group('base.group_system') or record.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user can not be set as a read-only..!'))
        return res


    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        res = super(res_users, cls)._login(db, login, password, user_agent_env=user_agent_env)
        try:            
            with cls.pool.cursor() as cr:   
                self = api.Environment(cr, res, {})[cls._name] 

                result = search_data(self, 'access.management',condition=('disable_login','=',True), operator='AND', limit=1)
                if result:
                    raise AccessDenied("Login is disabled for this user due to access management settings.")
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from ", db, login)
            raise
        return res
        
