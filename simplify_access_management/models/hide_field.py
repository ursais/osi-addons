from odoo import fields, models, api, _
from lxml import etree


class hide_field(models.Model):
    _name = 'hide.field'
    _description = "Fields Rights"

    access_management_id = fields.Many2one('access.management', 'Access Management')

    model_id = fields.Many2one('ir.model', 'Model')

    field_id = fields.Many2many('ir.model.fields', 'hide_field_ir_model_fields_rel', 'hide_field_id', 'ir_field_id',
                                'Field')

    invisible = fields.Boolean('Invisible', help="Selected Field will be hidden in selected model from the defined users.")
    readonly = fields.Boolean('Read-Only', help="Selected Field will be Read only in selected model from the defined users.")
    required = fields.Boolean('Required', help="Selected Field will be set as required for selected model from the defined users.")
    external_link = fields.Boolean('Remove External Link', help="External Link will be hidden for relational fields in selected model from the defined users.")

