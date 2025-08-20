from odoo import models, api, SUPERUSER_ID, _
from odoo.tools.translate import _
from odoo.http import request
import ast
from .query_prepare import search_data

class ir_ui_view(models.Model):
    _inherit = 'ir.ui.view'

    def _postprocess_tag_field(self, node, name_manager, node_info):
        super()._postprocess_tag_field(node, name_manager, node_info)
        try:
            

            hide_fields = search_data(self, 'hide.field', name_manager.model._name)
            if node.tag == 'field' or node.tag == 'label':
                for hide_field in hide_fields:
                    for field_id in hide_field.field_id:
                        if (node.tag == 'field' and node.get('name') == field_id.name) or (
                                node.tag == 'label' and 'for' in node.attrib.keys() and node.attrib[
                            'for'] == field_id.name):
                            if hide_field.external_link:
                                options_dict = {}
                                if 'widget' in node.attrib.keys():
                                    if node.attrib['widget'] == 'product_configurator' or node.attrib['widget'] == 'many2one_avatar_user':
                                        del node.attrib['widget']
                                        
                                if 'options' in node.attrib.keys():
                                    options_dict = ast.literal_eval(node.attrib['options'])
                                    options_dict.update({"no_edit": True, "no_create": True, "no_open": True})
                                    node.attrib['options'] = str(options_dict)
                                else:
                                    options_dict.update({'no_create': True, 'no_edit': True,'no_open': True})
                                    node.attrib['options'] = str(options_dict)
                                    
                                    
                            if hide_field.invisible:
                                node_info['column_invisible'] = True
                                node.set('column_invisible', 'True')
                                node_info['invisible'] = True
                                node.set('invisible', '1')
                            if hide_field.readonly:
                                node_info['readonly'] = True
                                node.set('readonly', '1')
                                node.set('force_save', '1')
                            if hide_field.required:
                                node_info['required'] = True
                                node.set('required', '1')

            
        except Exception:
            pass

    def _postprocess_tag_button(self, node, name_manager, node_info):
        # Hide Any Button
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_button', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_button(node, name_manager, node_info)

        hide = None
        
        hide_button_ids = search_data(self, 'hide.view.nodes', name_manager.model._name)
        # Filtered with same env user and current model
        btn_store_model_nodes_ids = hide_button_ids.mapped('btn_store_model_nodes_ids') if hide_button_ids else False
        # translation_obj = self.env['ir.translation']
        if btn_store_model_nodes_ids:
            for btn in btn_store_model_nodes_ids:
                if btn.attribute_name == node.get('name'):
                    hide = [btn]
                    break
                    
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']
            node_info['invisible'] = True

        return None

    def _postprocess_tag_page(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_page', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide = None
        
        hide_tab_ids = search_data(self, 'hide.view.nodes', name_manager.model._name)
        page_store_model_nodes_ids = hide_tab_ids.mapped('page_store_model_nodes_ids') if hide_tab_ids else False
        if page_store_model_nodes_ids:

            for tab in page_store_model_nodes_ids:
                attribute_string = tab.attribute_string
                if tab.lang_code != self.env.lang:
                    field = self.env['ir.ui.view']._fields['arch_db']
                    translation_dictionary = field.get_translation_dictionary(
                        self.with_context(lang=tab.lang_code).arch_db,
                        {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']})
                    attribute_string = translation_dictionary[attribute_string][self.env.lang]
                    if not attribute_string:
                        if tab.attribute_name == node.attrib.get('name'):
                            hide = [tab]
                            break
                if attribute_string == node.get('string'):
                    hide = [tab]
                    break
                    
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']

            node_info['invisible'] = True

        return None

    def _postprocess_tag_a(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_a', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide = None
       
        hide_tab_ids = search_data(self, 'hide.view.nodes', name_manager.model._name)
        link_store_model_nodes_ids = hide_tab_ids.mapped('link_store_model_nodes_ids') if hide_tab_ids else False
        if link_store_model_nodes_ids:
            for link in link_store_model_nodes_ids:
                
                if _(link.attribute_name) == node.get('name'):
                    hide = [link]
                    break
                      
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']

            node_info['invisible'] = True

        return None

    def _postprocess_tag_div(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_div', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        setting_tabs = search_data(self, 'hide.view.nodes', name_manager.model._name)
        if name_manager.model._name == 'res.config.settings' and node.tag == 'app' and node.get('string'):
            setting_tabs = setting_tabs.mapped('page_store_model_nodes_ids') if setting_tabs else False
            for setting_tab in setting_tabs:
                attribute_string = setting_tab.attribute_string
                if setting_tab.lang_code != self.env.lang:
                    field = self.env['ir.ui.view']._fields['arch_db']
                    translation_dictionary = field.get_translation_dictionary(
                        self.with_context(lang=setting_tab.lang_code).arch_db,
                        {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']})
                    attribute_string = translation_dictionary[attribute_string][self.env.lang]
                if node.get('data-key') == setting_tab.attribute_name:
                    node_info['invisible'] = True
                    node.set('invisible', '1')

        return None

    def _postprocess_tag_filter(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_filter', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        if node.tag == 'filter' or node.tag == 'group':
            
            hide_filter_group_obj = search_data(self, 'hide.filters.groups', name_manager.model._name)
            if hide_filter_group_obj:
                for hide_field_obj in hide_filter_group_obj:
                    for hide_filter in hide_field_obj.filters_store_model_nodes_ids.mapped('attribute_name'):
                        if hide_filter == node.get('name', False):
                            node_info['invisible'] = True
                            node.set('invisible', '1')
                    for hide_field_obj in hide_filter_group_obj:
                        for hide_filter in hide_field_obj.groups_store_model_nodes_ids.mapped('attribute_name'):
                            if hide_filter == node.get('name', False):
                                node_info['invisible'] = True
                                node.set('invisible', '1')
        return None
        
    def _postprocess_tag_label(self, node, name_manager, node_info):
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_label', False)
        hide_field_obj = self.env['hide.field'].sudo()
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_label(node, name_manager, node_info)
            if node.get('for'):
                hide_lable = search_data(self, 'hide.field', name_manager.model._name)
                if hide_lable:
                    for hide_field in hide_lable:
                        for field_id in hide_field.field_id:
                            if node.get('for') == field_id.name and node.get('string') == field_id.field_description:
                                node_info['invisible'] = True
                                node.set('invisible', '1')

            

