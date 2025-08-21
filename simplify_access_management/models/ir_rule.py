# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import  ValidationError, UserError
from odoo.tools import config
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.http import request
from datetime import datetime,timedelta
from odoo.tools import SQL, Query
from dateutil.relativedelta import relativedelta
from odoo.addons.advanced_web_domain_widget.models.domain_prepare import prepare_domain_v2,compute_domain
import ast

class ir_rule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    @tools.conditional(
        'xml' not in config['dev_mode'],
        tools.ormcache('self.env.uid', 'self.env.su', 'model_name', 'mode',
                       'tuple(self._compute_domain_context_values())'),
    )
    def _compute_domain(self, model_name, mode="read"):
        res = super(ir_rule, self)._compute_domain(model_name, mode)

        read_value = True
        self._cr.execute(SQL("SELECT state FROM ir_module_module WHERE name='simplify_access_management'"))
        data = self._cr.fetchone() or False

        self._cr.execute(SQL("SELECT id FROM ir_module_module WHERE state IN ('to upgrade', 'to remove','to install')"))
        all_data = self._cr.fetchone() or False

        if data and data[0] != 'installed':
            read_value = False
        model_list = ['mail.activity', 'res.users.log', 'res.users', 'mail.channel', 'mail.alias', 'bus.presence',
                      'res.lang']

        if self.env.user.id and read_value and not all_data:
            if model_name not in model_list:
                # self._cr.execute(SQL("""SELECT am.id FROM access_management as am
                #                     WHERE active='t' AND readonly = True AND am.id 
                #                     IN (SELECT au.access_management_id 
                #                         FROM access_management_users_rel_ah as au 
                #                         WHERE user_id = %s AND am.id 
                #                         IN (SELECT ac.access_management_id
                #                             FROM access_management_comapnay_rel as ac)) """ % (self.env.user.id))) 
                
                # a = self._cr.fetchall()
                a = self.env['access.management'].sudo().browse(
                            row[0] for row in self._cr.fetchall())
                if a:
                    a -= a.filtered(lambda x: x.is_apply_on_without_company == False and self.env.company.id not in x.company_ids.ids)
                    if bool(a):
                        if mode != 'read' and model_name not in ['mail.channel.partner']:
                            raise UserError(
                                _('%s is a read-only user. So you can not make any changes in the system!') % self.env.user.name)
        value = self._cr.execute(SQL(
            """SELECT value from ir_config_parameter where key='uninstall_simplify_access_management' """))
        value = self._cr.fetchone()
        if not value:
            value = self._cr.execute(SQL("""select state from ir_module_module where name = 'simplify_access_management'"""))
            value = self._cr.fetchone()
            value = value and value[0] or False
            
            if model_name and model_name in self.env and value == 'installed':
                self._cr.execute(SQL("SELECT id FROM ir_model WHERE model='%s'" % model_name))
                model_numeric_id = self._cr.fetchone()
                model_numeric_id = model_numeric_id and model_numeric_id[0] or False
                if model_numeric_id and isinstance(model_numeric_id, int) and self.env.user:
                    try:
                        self._cr.execute(SQL("""
                                        SELECT dm.id
                                        FROM access_domain_ah as dm
                                        WHERE dm.model_id=%s AND dm.apply_domain AND dm.access_management_id 
                                        IN (SELECT am.id 
                                            FROM access_management as am 
                                            WHERE active='t' AND am.id 
                                            IN (SELECT amusr.access_management_id
                                                FROM access_management_users_rel_ah as amusr
                                                WHERE amusr.user_id=%s))
                                        """% (model_numeric_id, self.env.user.id)))
                    
                        access_domain_ah_ids = self.env['access.domain.ah'].sudo().browse(
                            row[0] for row in self._cr.fetchall())
                        
                        access_domain_ah_ids -= access_domain_ah_ids.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)
                    # access_domain_ah_ids = access_domain_ah_ids.filtered(lambda line: self.env.company in line.access_management_id.company_ids)
                    except:
                        access_domain_ah_ids = False
                    if access_domain_ah_ids:
                        domain_list = []
                        if model_name == 'res.partner':
                            # jo aya user related jetala partner 6 ana access alag thi apididha 6 error no ave atle
                            self._cr.execute(SQL("""SELECT partner_id FROM res_users"""))
                            partner_ids = [row[0] for row in self._cr.fetchall()]
                            if len(domain_list) > 1:
                                domain_list.insert(0, '|')
                            domain_list += ['|',('id', 'in', partner_ids)]
                        left_user = False
                        # only domain records
                        length = len(access_domain_ah_ids.sudo()) if access_domain_ah_ids.sudo() else 0
                        
                        for access in access_domain_ah_ids.sudo():
                            dom = ast.literal_eval(access.domain) if access.domain else []
                            if not dom and isinstance(dom,list):
                                if length>1:
                                    domain_list.insert(0,'|')
                                domain_list += [('id', '!=', False)]
                                length -= 1
                        
                            if dom:
                                dom = expression.normalize_domain(dom)
                                for dom_tuple in dom:
                                    if isinstance(dom_tuple, tuple):
                                        compute_domain(dom_tuple,model_name)
                                        operator_value = dom_tuple[1]
                                       
                                        if operator_value == 'date_filter':
                                            domain_list += prepare_domain_v2(dom_tuple)
                                           
                                        else:
                                            domain_list.append(dom_tuple)
                                    else:
                                        domain_list.append(dom_tuple)
                                if length > 1:
                                    domain_list.insert(0, '|')
                                    length -= 1
                                
                        if domain_list:
                            return domain_list

        return res
