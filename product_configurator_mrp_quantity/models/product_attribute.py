from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    is_qty_required = fields.Boolean(string="Qty Required", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        template_attribute_value_obj = self.env["product.template.attribute.value"]
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        for val in vals_list:
            if result.is_qty_required and result.value_ids:
                qty_list = []
                for attr_value in result.value_ids:
                    template_attri_value_id = template_attribute_value_obj.search(
                        [
                            ("product_tmpl_id", "=", result.product_tmpl_id.id),
                            ("attribute_line_id", "=", result.id),
                            ("product_attribute_value_id", "=", attr_value.id),
                            ("attribute_id", "=", result.attribute_id.id),
                        ]
                    )
                    qty_list.append(
                        {
                            "product_tmpl_id": result.product_tmpl_id.id,
                            "product_attribute_id": result.attribute_id.id,
                            "product_attribute_value_id": attr_value.id,
                            "qty": template_attri_value_id.default_qty,
                            "template_attri_value_id": template_attri_value_id.id,
                        }
                    )
                attribute_value_qty_obj.create(qty_list)
        return result

    def write(self, values):
        result = super().write(values)
        template_attribute_value_obj = self.env["product.template.attribute.value"]
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        attribute_value_line_domain = [
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
            ("attribute_line_id", "=", self.id),
            ("attribute_id", "=", self.attribute_id.id),
        ]
        if values.get("is_qty_required") and self.value_ids:
            qty_list = []
            for attr_value in self.value_ids:
                attribute_value_line_domain += [
                    ("product_attribute_value_id", "=", attr_value.id)
                ]
                template_attri_value_id = template_attribute_value_obj.search(
                    attribute_value_line_domain
                )
                qty_list.append(
                    {
                        "product_tmpl_id": self.product_tmpl_id.id,
                        "product_attribute_id": self.attribute_id.id,
                        "product_attribute_value_id": attr_value.id,
                        "qty": template_attri_value_id.default_qty,
                        "template_attri_value_id": template_attri_value_id.id,
                    }
                )
            attribute_value_qty_obj.create(qty_list)
        elif values.get("is_qty_required") == False:
            for attr_value in self.value_ids:
                attribute_value_line_domain += [
                    ("product_attribute_value_id", "=", attr_value.id)
                ]
                template_attri_value_id = template_attribute_value_obj.search(
                    attribute_value_line_domain
                )
                template_attri_value_id.attribute_value_qty_ids.unlink()
        return result


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
