# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FieldsExternalHelp(models.Model):
    _name = 'fields.external.help'
    _description = 'Fields External Help'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        string="Model",
        comodel_name="ir.model",
        ondelete="cascade",
        required=True,
        help="Model for the Fields Help.")
    model = fields.Char(related='model_id.model', readonly=True)
    help_line_ids = fields.One2many(
        string="Fields Helps",
        comodel_name="field.help.line",
        inverse_name="external_help_id",
        help="Fields Help Line.")

    @api.constrains('model_id', 'help_line_ids')
    def _check_duplicate_entries(self):
        fields_help_obj = self.env['fields.external.help']
        for rec in self:
            if fields_help_obj.search([('model_id', '=', rec.model_id.id),
                                       ('id', '!=', rec.id)]):
                raise ValidationError(_("Help has been already added \
                    for the model: {}").format(rec.model_id.name))
            fields_list = [field.field_id.id for field in rec.help_line_ids]
            if set([x for x in fields_list if
                    fields_list.count(x) > 1]):
                raise ValidationError(_("You can not add duplicate\
                    help for one field!"))
