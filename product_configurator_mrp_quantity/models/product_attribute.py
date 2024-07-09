from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    is_qty_required = fields.Boolean(string="Qty Required", copy=False)


class ProductAttributePrice(models.Model):
    _inherit = "product.template.attribute.value"

    is_qty_required = fields.Boolean(
        related="attribute_line_id.is_qty_required",
        store=True,
        string="Qty Required",
        copy=False,
    )
    default_qty = fields.Integer("Default Quantity", default=1)
    maximum_qty = fields.Integer("Max Quantity", default=1)

    @api.constrains("default_qty", "maximum_qty")
    def _check_default_qty_maximum_qty(self):
        for rec in self:
            if rec.default_qty > rec.maximum_qty:
                raise ValidationError(
                    _("Maximum Qty can't be smaller then Default Qty")
                )
