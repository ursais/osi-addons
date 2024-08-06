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
    attribute_value_qty_ids = fields.One2many(
        "attribute.value.qty", "template_attri_value_id", string="Value Quantity"
    )

    @api.constrains("default_qty", "maximum_qty")
    def _check_default_qty_maximum_qty(self):
        for rec in self:
            if rec.default_qty > rec.maximum_qty:
                raise ValidationError(
                    _("Maximum Qty can't be smaller then Default Qty")
                )

    def update_attribute_value_qty(self):
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        for result in self:
            if result.is_qty_required:
                val_list = []
                existing_rec = attribute_value_qty_obj.search(
                    [
                        ("product_tmpl_id", "=", result.product_tmpl_id.id),
                        ("product_attribute_id", "=", result.attribute_id.id),
                        (
                            "product_attribute_value_id",
                            "=",
                            result.product_attribute_value_id.id,
                        ),
                    ]
                )
                existing_rec.unlink()
                for i in range(result.default_qty, result.maximum_qty + 1):
                    val_list.append(
                        {
                            "name": result.product_tmpl_id.name,
                            "product_tmpl_id": result.product_tmpl_id.id,
                            "product_attribute_id": result.attribute_id.id,
                            "product_attribute_value_id": result.product_attribute_value_id.id,
                            "template_attri_value_id": result.id,
                            "qty": i,
                        }
                    )
                attribute_value_qty_obj.create(val_list)
