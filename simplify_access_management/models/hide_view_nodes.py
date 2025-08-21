from odoo import fields, models, api, _
from odoo.tools.translate import TranslationModuleReader
from lxml import etree


class hide_view_nodes(models.Model):
    _name = 'hide.view.nodes'
    _description = 'Hide View Nodes'

    model_id = fields.Many2one(
        'ir.model', string='Model', index=True, required=True, ondelete='cascade')

    model_name = fields.Char(string='Model Name', related='model_id.model', readonly=True, store=True)

    btn_store_model_nodes_ids = fields.Many2many('store.model.nodes', 'btn_hide_view_nodes_store_model_nodes_rel',
                                                 'hide_id', 'store_id', string='Hide Button',
                                                 domain="[('node_option','=','button')]",
                                                 help="The Buttons are added on list will be hidden in selected model from the defined users.")
    page_store_model_nodes_ids = fields.Many2many('store.model.nodes', 'page_hide_view_nodes_store_model_nodes_rel',
                                                  'hide_id', 'store_id', string='Hide Tab/Page',
                                                  domain="[('node_option','=','page')]",
                                                  help="The Tabs(pages) are added on list will be hidden in selected model from the defined users.")
    link_store_model_nodes_ids = fields.Many2many('store.model.nodes', 'link_hide_view_nodes_store_model_nodes_rel',
                                                  'hide_id', 'store_id', string='Hide Kanban Link',
                                                  domain="[('node_option','=','link')]",
                                                  help="The Kanban view action are added on list will be hidden in selected model from the defined users.")

    access_management_id = fields.Many2one('access.management', 'Access Management')

    def _store_btn_data(self, btn, smart_button=False, smart_button_string=False):
        # string_value is used in case of kanban view button store, 
        string_value = 'string_value' in self._context.keys() and self._context['string_value'] or False

        store_model_button_obj = self.env['store.model.nodes'].sudo()
        name = btn.get('string') or string_value
        if smart_button:
            name = smart_button_string
        store_model_button_obj.create({
            'model_id': self.model_id.id,
            'node_option': 'button',
            'attribute_name': btn.get('name'),
            'attribute_string': name,
            'button_type': btn.get('type'),
            'is_smart_button': smart_button,
            'lang_code': self.env.lang,
        })

    def _get_smart_btn_string(self, btn_list, type=False):
        store_model_button_obj = self.env['store.model.nodes'].sudo()

        def _get_span_text(span_list):
            name = ''
            for sp in span_list:
                if sp.text:
                    name = name + ' ' + sp.text
            name = name.strip()
            return name

        for btn in btn_list:
            name = ''
            field_list = btn.findall('field')
            if field_list:
                name = field_list[0].get('string')
            else:
                span_list = btn.findall('span')
                if span_list:
                    name = _get_span_text(span_list)
                else:
                    div_list = btn.findall('div')
                    if div_list:
                        span_list = div_list[0].findall('span')
                        if span_list:
                            name = _get_span_text(span_list)
            if not name:
                try:
                    name = btn.get('string')
                except:
                    pass
            if name and (type == 'object' or type == 'action'):
                domain = [('button_type', '=', btn.get('type')), ('attribute_string', '=', name),
                          ('model_id', '=', self.model_id.id), ('node_option', '=', 'button')]
                if type == 'object':
                    domain += [('attribute_name', '=', btn.get('name'))]
                if type == 'action':
                    domain += [('attribute_name', '=', btn.get('name'))]
                smart_button_id = store_model_button_obj.search(domain)
                if not smart_button_id:
                    self._store_btn_data(btn, smart_button=True, smart_button_string=name)
                else:
                    smart_button_id[0].is_smart_button = True

    @api.model
    @api.onchange('model_id')
    def _get_button(self):
        store_model_nodes_obj = self.env['store.model.nodes'].sudo()
        view_obj = self.env['ir.ui.view'].sudo()

        if self.model_id and self.model_name:

            view_list = ['form', 'tree', 'kanban']
            for view in view_list:
                for views in view_obj.search([('model', '=', self.model_name), ('type', '=', view)]):
                    res = self.env[self.model_name].sudo().get_view(view_id=views.id, view_type=view)
                    doc = etree.XML(res['arch'])

                    object_link = doc.xpath("//a")
                    for btn in object_link:
                        if btn.text and '\n' not in btn.text and 'type' in btn.attrib.keys() and btn.attrib[
                            'type'] and 'name' in btn.attrib.keys() and btn.attrib['name']:
                            domain = [('button_type', '=', btn.get('type')), ('attribute_string', '=', btn.text),
                                      ('attribute_name', '=', btn.get('name')), ('model_id', '=', self.model_id.id),
                                      ('node_option', '=', 'link')]
                            if not store_model_nodes_obj.search(domain):
                                store_model_nodes_obj.create({
                                    'model_id': self.model_id.id,
                                    'node_option': 'link',
                                    'attribute_name': btn.get('name'),
                                    'attribute_string': btn.text,
                                    'button_type': btn.get('type'),
                                    'lang_code': self.env.lang,
                                })

                    object_button = doc.xpath("//button[@type='object']")
                    for btn in object_button:
                        string_value = btn.get('string')
                        if view == 'kanban' and not string_value:
                            try:
                                string_value = btn.text if not btn.text.startswith('\n') else False
                            except:
                                pass

                        if not string_value:
                            fields = btn.findall(".//*[@class='o_stat_text']")
                            if fields:
                                string_value = ""
                            for f in fields:
                                if f.text:
                                    string_value += " " + f.text

                        if btn.get('name') and string_value:
                            domain = [('button_type', '=', btn.get('type')), ('attribute_string', '=', string_value),
                                      ('attribute_name', '=', btn.get('name')), ('model_id', '=', self.model_id.id),
                                      ('node_option', '=', 'button')]
                            if not store_model_nodes_obj.search(domain):
                                self.with_context(string_value=string_value)._store_btn_data(btn)

                    action_button = doc.xpath("//button[@type='action']")
                    for btn in action_button:
                        string_value = btn.get('string')
                        if view == 'kanban' and not string_value:
                            try:
                                string_value = btn.text if not btn.text.startswith('\n') else False
                            except:
                                pass
                        if btn.get('name') and string_value:
                            domain = [('button_type', '=', btn.get('type')), ('attribute_string', '=', string_value),
                                      ('attribute_name', '=', btn.get('name')), ('model_id', '=', self.model_id.id),
                                      ('node_option', '=', 'button')]
                            if not store_model_nodes_obj.search(domain):
                                self.with_context(string_value=string_value)._store_btn_data(btn)

                    if view == 'form':
                        # Smart Buttons Extraction
                        smt_button_division = doc.xpath("//div[@class='oe_button_box']")
                        if smt_button_division:
                            smt_button_division = etree.tostring(smt_button_division[0])
                            smt_button_division = etree.XML(smt_button_division)

                            smt_object_button = smt_button_division.xpath("//button[@type='object']")
                            self._get_smart_btn_string(smt_object_button, type='object')

                            smt_action_button = smt_button_division.xpath("//button[@type='action']")
                            self._get_smart_btn_string(smt_action_button, type='action')

                        # Tab Extraction
                        page_list = doc.xpath("//page")
                        if page_list:
                            for page in page_list:
                                if page.get('string'):
                                    domain = [('attribute_string', '=', page.get('string')),
                                              ('model_id', '=', self.model_id.id), ('node_option', '=', 'page')]
                                    if page.get('name'):
                                        domain += [('attribute_name', '=', page.get('name'))]
                                    store_model_nodes_id = store_model_nodes_obj.search(domain, limit=1)
                                    if not store_model_nodes_id:
                                        store_model_nodes_obj.create({
                                            'model_id': self.model_id.id,
                                            'attribute_name': page.get('name'),
                                            'attribute_string': page.get('string'),
                                            'node_option': 'page',
                                            'lang_code': self.env.lang,
                                        })
                        if self.model_name == 'res.config.settings':
                            for setting_page in doc.xpath("//app"):
                                if setting_page.get('string'):
                                    domain = [('attribute_string', '=', setting_page.get('string')),
                                              ('model_id', '=', self.model_id.id), ('node_option', '=', 'page')]
                                    if setting_page.get('name'):
                                        domain += [('attribute_name', '=', setting_page.get('name'))]
                                    store_model_nodes_id = store_model_nodes_obj.search(domain, limit=1)
                                    if not store_model_nodes_id:
                                        store_model_nodes_obj.create({
                                            'model_id': self.model_id.id,
                                            'attribute_name': setting_page.get('name') or '',
                                            'attribute_string': setting_page.get('string'),
                                            'node_option': 'page',
                                            'lang_code': self.env.lang,
                                        })


class store_model_nodes(models.Model):
    _name = 'store.model.nodes'
    _description = 'Store Model Nodes'
    _rec_name = 'attribute_string'

    model_id = fields.Many2one('ir.model', string='Model', index=True, ondelete='cascade', required=True)
    node_option = fields.Selection([('button', 'Button'), ('page', 'Page'), ('link', 'Link')], string="Node Option",
                                   required=True)
    attribute_name = fields.Char('Attribute Name')
    attribute_string = fields.Char('Attribute String', required=True, translate=True)
    lang_code = fields.Char("Language Code")
    button_type = fields.Selection([('object', 'Object'), ('action', 'Action')], string="Button Type")
    is_smart_button = fields.Boolean('Smart Button')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.attribute_string
            if rec.attribute_name:
                name = name + ' (' + rec.attribute_name + ')'
                if rec.is_smart_button and rec.node_option == 'button':
                    name = name + ' (Smart Button)'
            result.append((rec.id, name))
        return result
