from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.http import request
from .query_prepare import search_data

class access_management(models.Model):
    _name = 'access.management'
    _description = "Access Management"

    name = fields.Char('Name')
    user_ids = fields.Many2many('res.users', 'access_management_users_rel_ah', 'access_management_id', 'user_id',
                                'Users')

    readonly = fields.Boolean('Read-Only')
    active = fields.Boolean('Active', default=True)

    hide_menu_ids = fields.Many2many('menu.item', 'access_management_menu_rel_ah', 'access_management_id', 'menu_id',
                                     'Hide Menu',
                                     help="The menu or submenu added on above list will be hidden from the defined users.")
    hide_field_ids = fields.One2many('hide.field', 'access_management_id', 'Hide Field', copy=True)

    remove_action_ids = fields.One2many('remove.action', 'access_management_id', 'Remove Action', copy=True)

    access_domain_ah_ids = fields.One2many('access.domain.ah', 'access_management_id', 'Access Domain', copy=True)
    hide_view_nodes_ids = fields.One2many('hide.view.nodes', 'access_management_id', 'Button/Tab Access', copy=True)

    self_module_menu_ids = fields.Many2many('ir.ui.menu', 'access_management_ir_ui_self_module_menu',
                                            'access_management_id', 'menu_id', 'Self Module Menu',
                                            default=lambda self: self.env.ref('simplify_access_management.main_menu_simplify_access_management'))
   
    total_rules = fields.Integer('Access Rules', compute="_count_total_rules")

    # Chatter
    hide_chatter_ids = fields.One2many('hide.chatter', 'access_management_id', 'Hide Chatters', copy=True)

    hide_chatter = fields.Boolean('Hide Chatter',
                                  help="The Chatter will be hidden in all model from the specified users.")
    hide_send_mail = fields.Boolean('Hide Send Message',
                                    help="The Send Message button will be hidden in chatter of all model from the specified users.")
    hide_log_notes = fields.Boolean('Hide Log Notes',
                                    help="The Log Notes button will be hidden in chatter of all model from the specified users.")
    hide_schedule_activity = fields.Boolean('Hide Schedule Activity',
                                            help="The Schedule Activity button will be hidden in chatter of all model from the specified users.")

    hide_export = fields.Boolean(help="The Export button will be hidden in all model from the specified users.")
    hide_import = fields.Boolean(help="The Import button will be hidden in all model from the specified users.")
    hide_spreadsheet = fields.Boolean()
    hide_add_property = fields.Boolean()
    disable_login = fields.Boolean('Disable Login',help="The Users can not login if this button is chek.")

    disable_debug_mode = fields.Boolean('Disable Developer Mode',
                                        help="Developer mode will be hidden from the defined users.")

    company_ids = fields.Many2many('res.company', 'access_management_comapnay_rel', 'access_management_id',
                                   'company_id', 'Companies', default=lambda self: self.env.company)

    hide_filters_groups_ids = fields.One2many('hide.filters.groups', 'access_management_id', 'Hide Filters/Group By',
                                              copy=True)
    is_apply_on_without_company = fields.Boolean(string="Apply Without Company", default=True,help="When 'Apply Without Company' is selected, the rules will be applied to every company.")
    def _count_total_rules(self):
        for rec in self:
            rule = 0
            rule = rule + len(rec.hide_menu_ids) + len(rec.hide_field_ids) + len(rec.remove_action_ids) + len(
                rec.access_domain_ah_ids) + len(rec.hide_view_nodes_ids)
            rec.total_rules = rule

    def action_show_rules(self):
        pass

    def toggle_active_value(self):
        for record in self:
            record.write({'active': not record.active})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        res = super(access_management, self).create(vals_list)
 
        request.registry.clear_cache()
        for record in res:
            if record.readonly:
                for user in record.user_ids:
                    if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user can not be set as a read-only..!'))
        return res

    def unlink(self):
        res = super(access_management, self).unlink()
        request.env.registry.clear_cache()
     
        return res

    def write(self, vals):
        res = super(access_management, self).write(vals)

        if any(self.mapped('readonly')):
            for user in self.user_ids:
                if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                    raise UserError(_('Admin user can not be set as a read-only..!'))
        request.env.registry.clear_cache()
        return res

    def get_remove_options(self, model):
        
        restrict_export = search_data(self, self._name, model, ('hide_export','=',True), 'AND')

        remove_action = search_data(self, 'remove.action', model)
        options = []
        added_export = False

        if restrict_export:
            options.append('export')
            added_export = True

        if remove_action:
            for action in remove_action:
                if not added_export and action.restrict_export:
                    options.append('export')
                if action.restrict_archive_unarchive:
                    options.append('archive')
                    options.append('unarchive')
                if action.restrict_duplicate:
                    options.append('duplicate')
        return options

    @api.model
    def get_chatter_hide_details(self, user_id, company_id, model=False):
        hide_send_mail = hide_log_notes = hide_schedule_activity = True

        chatter_access_id = search_data(self, self._name, condition=('hide_chatter','=',True), operator='AND', limit=1)
        if chatter_access_id:
            return {'hide_send_mail': False, 'hide_log_notes': False, 'hide_schedule_activity': False}
        else:
            hide_send_mail_id = search_data(self, self._name, condition=('hide_send_mail','=',True), operator='AND',limit=1)
            if hide_send_mail_id:
                hide_send_mail = False
            hide_log_notes_id = search_data(self, self._name, condition=('hide_log_notes','=',True), operator='AND',limit=1)
            if hide_log_notes_id:
                hide_log_notes = False
            hide_schedule_activity_id = search_data(self, self._name, condition=('hide_schedule_activity','=',True), operator='AND',limit=1)
            if hide_schedule_activity_id:
                hide_schedule_activity = False
            

        if model:
            hide_ids = search_data(self, 'hide.chatter', model, condition=('hide_chatter','=',True), operator='AND', limit=1)
            if hide_ids:
                return {'hide_send_mail': False, 'hide_log_notes': False, 'hide_schedule_activity': False}
            else:
                if hide_send_mail:
                    hide_send_mail_id = search_data(self, 'hide.chatter', model, condition=('hide_send_mail','=',True), operator='AND',limit=1)
                    if hide_send_mail_id:
                        hide_send_mail = False
                if hide_log_notes:
                    hide_log_notes_id = search_data(self, 'hide.chatter', model, condition=('hide_log_notes','=',True), operator='AND',limit=1)
                    if hide_log_notes_id:
                        hide_log_notes = False
                if hide_schedule_activity:
                    hide_schedule_activity_id = search_data(self, 'hide.chatter', model, condition=('hide_schedule_activity','=',True), operator='AND',limit=1)
                    if hide_schedule_activity_id:
                        hide_schedule_activity = False

                if hide_log_notes and hide_ids.filtered(lambda x: x.hide_log_notes):
                    hide_log_notes = False

                if hide_schedule_activity and hide_ids.filtered(lambda x: x.hide_schedule_activity):
                    hide_schedule_activity = False

        return {
            'hide_send_mail': hide_send_mail,
            'hide_log_notes': hide_log_notes,
            'hide_schedule_activity': hide_schedule_activity
        }
        

    def is_spread_sheet_available(self, action_model, action_id):
        if action_model and action_id:
            model = self.env[action_model].sudo().browse(action_id).res_model
            hide_spreadsheet = search_data(self, self._name, model, ('hide_spreadsheet','=',True), 'AND',limit=1)
            
            if hide_spreadsheet:
                return True
            
            if model:
                restrict_spreadsheet = search_data(self, 'remove.action', model, ('restrict_spreadsheet','=',True), 'AND')
                if restrict_spreadsheet:
                    return True

        return False

    def is_add_property_available(self, model):
        hide_property = search_data(self, self._name, model, ('hide_add_property','=',True), 'AND')
        if hide_property:
            return True
        return False
 

    def get_hidden_field(self, model=False):
        if model:
            hidden_fields = []
           
            hide_fields = search_data(self, 'hide.field', model, ('invisible','=',True), 'AND')
            for hide_field in hide_fields:
                for field in hide_field.field_id:
                    if field.name:
                        hidden_fields.append(field.name)
            return hidden_fields
        return []
