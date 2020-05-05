# See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.exceptions import ValidationError

class FieldHelpLine(models.Model):
    _name = "field.help.line"
    _description = "Field Help Line"

    field_id = fields.Many2one(
        string="Field name",
        required=True,
        comodel_name="ir.model.fields",
        ondelete="set null")
    field_name = fields.Char(related="field_id.name", readonly=True)
    external_url = fields.Char(
        string="External Url")
    external_help_id = fields.Many2one(
        string="External Help",
        comodel_name="fields.external.help",
        ondelete="cascade")
    model_id = fields.Many2one(
        related='external_help_id.model_id', readonly=True)
    model = fields.Char(related='model_id.model', readonly=True)
    link_text = fields.Char(string="Link Text")
    help_text = fields.Html(string="Help Text")
