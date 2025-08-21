# -*- coding: utf-8 -*-
import logging
from odoo.http import request
from odoo import api, models, tools, _, _lt
from odoo.exceptions import ValidationError, AccessError
from odoo.tools import SQL, Query

_logger = logging.getLogger(__name__)


class ir_model_access(models.Model):
    _inherit = 'ir.model.access'
    

    @api.model
    def check(self, model, mode='read', raise_exception=True):
        if self.env.su:
            # User root have all accesses
            return True

        assert isinstance(model, str), 'Not a model name: %s' % (model,)

        # TransientModel records have no access rights, only an implicit access rule
        is_model_exists = True
        if model not in self.env:
            _logger.error('Missing model %s', model)
            is_model_exists = False

        has_access = model in self._get_allowed_models(mode)

        try:
            value = self._cr.execute(SQL(
                """SELECT value from ir_config_parameter where key='uninstall_simplify_access_management' """))
            value = self._cr.fetchone()
            if not value:
                if is_model_exists:
                
                    self._cr.execute(SQL("SELECT id FROM ir_model WHERE model='%s'" % model))
                    model_numeric_id = self._cr.fetchone()[0]
                    if model_numeric_id and isinstance(model_numeric_id, int) and self.env.user:
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
                        if mode == 'read':
                            access_domain_ah_ids = access_domain_ah_ids.filtered(lambda x: x.read_right)
                        elif mode == 'create':
                            access_domain_ah_ids = access_domain_ah_ids.filtered(lambda x: x.create_right)
                        elif mode == 'write':
                            access_domain_ah_ids = access_domain_ah_ids.filtered(lambda x: x.write_right)
                        elif mode == 'unlink':
                            access_domain_ah_ids = access_domain_ah_ids.filtered(lambda x: x.delete_right)

                        if access_domain_ah_ids:
                            has_access = bool(access_domain_ah_ids)
        except:
            pass

        if not has_access and raise_exception:
            groups = '\n'.join('\t- %s' % g for g in self.group_names_with_access(model, mode))
            document_kind = self.env['ir.model']._get(model).name or model
            msg_heads = {
                # Messages are declared in extenso so they are properly exported in translation terms
                'read': _lt(
                    "You are not allowed to access '%(document_kind)s' (%(document_model)s) records.",
                    document_kind=document_kind,
                    document_model=model,
                ),
                'write':  _lt(
                    "You are not allowed to modify '%(document_kind)s' (%(document_model)s) records.",
                    document_kind=document_kind,
                    document_model=model,
                ),
                'create': _lt(
                    "You are not allowed to create '%(document_kind)s' (%(document_model)s) records.",
                    document_kind=document_kind,
                    document_model=model,
                ),
                'unlink': _lt(
                    "You are not allowed to delete '%(document_kind)s' (%(document_model)s) records.",
                    document_kind=document_kind,
                    document_model=model,
                ),
            }
            operation_error = msg_heads[mode]

            if groups:
                group_info = _("This operation is allowed for the following groups:\n%(groups_list)s", groups_list=groups)
            else:
                group_info = _("No group currently allows this operation.")

            resolution_info = _("Contact your administrator to request access if necessary.")

            _logger.info('Access Denied by ACLs for operation: %s, uid: %s, model: %s', mode, self._uid, model)
            msg = """{operation_error}

                {group_info}

                {resolution_info}""".format(
                operation_error=operation_error,
                group_info=group_info,
                resolution_info=resolution_info)

            raise AccessError(msg) from None
        try:
            read_value = True
            self._cr.execute(SQL("SELECT state FROM ir_module_module WHERE name='simplify_access_management'"))
            data = self._cr.fetchone() or False
            if data and data[0] != 'installed':
                read_value = False

            cids = int(request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split('-')[0] or request.env.company.id)
            if self.env.user.id and read_value and request.httprequest.cookies.get('cids'):
                
                self._cr.execute(SQL("""SELECT access_management_id FROM access_management_comapnay_rel WHERE company_id = %s"""% cids))
                a = self._cr.fetchall()
                if a:
                    self._cr.execute(SQL("""SELECT access_management_id FROM access_management_users_rel_ah WHERE user_id = %s AND access_management_id in %s""" % (self.env.user.id,tuple([i[0] for i in a] + [0]))))
                    a = self._cr.fetchall()
                    if a:
                        self._cr.execute(SQL("""SELECT id FROM access_management WHERE active='t' AND id in %s AND readonly = True""", (
                                    tuple([i[0] for i in a] + [0]))))
                        a = self._cr.fetchall()
                if bool(a):
                    if mode != 'read':
                        return False
        except:
            pass


        return has_access
