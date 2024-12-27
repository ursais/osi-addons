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
            qty_list = []
            for attribute in result:
                if attribute.is_qty_required and attribute.value_ids:
                    for attr_value in attribute.value_ids:
                        template_attri_value_id = template_attribute_value_obj.search(
                            [
                                ("product_tmpl_id", "=", attribute.product_tmpl_id.id),
                                ("attribute_line_id", "=", attribute.id),
                                ("product_attribute_value_id", "=", attr_value.id),
                                ("attribute_id", "=", attribute.attribute_id.id),
                            ]
                        )
                        for i in range(
                            template_attri_value_id.default_qty,
                            template_attri_value_id.maximum_qty + 1,
                        ):
                            qty_list.append(
                                {
                                    "product_tmpl_id": attribute.product_tmpl_id.id,
                                    "product_attribute_id": attribute.attribute_id.id,
                                    "product_attribute_value_id": attr_value.id,
                                    "qty": i,
                                    "template_attri_value_id": template_attri_value_id.id,
                                }
                            )
        attribute_value_qty_obj.create(qty_list)
        return result

    def _get_attribute_value_line_domain(self):
        return [
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
            ("attribute_line_id", "in", self.ids),
            ("attribute_id", "=", self.attribute_id.id),
        ]

    def write(self, values):
        result = super().write(values)
        template_attribute_value_obj = self.env["product.template.attribute.value"]
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        attribute_value_line_domain = [
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
            ("attribute_line_id", "in", self.ids),
            ("attribute_id", "=", self.attribute_id.id),
        ]
        if values.get("is_qty_required") and self.value_ids:
            qty_list = []
            for attr_value in self.value_ids:
                attribute_value_line_domain = self._get_attribute_value_line_domain()
                attribute_value_line_domain += [
                    ("product_attribute_value_id", "=", attr_value.id)
                ]
                template_attri_value_id = template_attribute_value_obj.search(
                    attribute_value_line_domain
                )
                for i in range(
                    template_attri_value_id.default_qty,
                    template_attri_value_id.maximum_qty + 1,
                ):
                    qty_list.append(
                        {
                            "product_tmpl_id": self.product_tmpl_id.id,
                            "product_attribute_id": self.attribute_id.id,
                            "product_attribute_value_id": attr_value.id,
                            "qty": i,
                            "template_attri_value_id": template_attri_value_id.id,
                        }
                    )
            attribute_value_qty_obj.create(qty_list)
        elif "is_qty_required" in values and not values.get("is_qty_required"):
            #is_check: Helping Variable for Server Action DB Migration
            is_check = bool(self.product_template_value_ids.filtered(lambda line: line.maximum_qty != 1 and line.is_qty_required)) 
            qty_variants = self.product_tmpl_id.product_variant_ids.filtered(
                lambda variant: variant.product_attribute_value_qty_ids.filtered(
                    lambda qty: qty.attr_value_id.attribute_id.id
                    == self.attribute_id.id
                )
            ) and is_check
            if qty_variants:
                raise ValidationError(
                    _(
                        "Qty Required cannot be disabled because there are variants that exist with quantities %s %s %s."
                        % (self.product_tmpl_id.display_name,self.attribute_id.name,self.id)
                    )
                )
            for attr_value in self.value_ids:
                attribute_value_line_domain = self._get_attribute_value_line_domain()
                attribute_value_line_domain += [
                    ("product_attribute_value_id", "=", attr_value.id)
                ]
                template_attri_value_id = template_attribute_value_obj.search(
                    attribute_value_line_domain
                )
                template_attri_value_id.attribute_value_qty_ids.unlink()
        return result

    @api.onchange("is_qty_required", "multi", "custom")
    def onchange_is_qty_required(self):
        if self.is_qty_required and (self.multi or self.custom):
            self.is_qty_required = False


class ProductAttributePrice(models.Model):
    _inherit = "product.template.attribute.value"

    is_qty_required = fields.Boolean(
        related="attribute_line_id.is_qty_required",
        store=True,
        string="Qty Required",
        copy=False,
    )
    default_qty = fields.Integer("Minimum Quantity", default=1)
    maximum_qty = fields.Integer("Maximum Quantity", default=2)
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

    def write(self, values):
        result = super().write(values)
        old_attribute_value_qty_ids = self.attribute_value_qty_ids
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        for res in self:
            if res.is_qty_required and (
                values.get("default_qty") or values.get("maximum_qty")
            ):
                qty_list = []
                for i in range(res.default_qty, res.maximum_qty + 1):
                    qty_list.append(
                        {
                            "product_tmpl_id": res.product_tmpl_id.id,
                            "product_attribute_id": res.attribute_id.id,
                            "product_attribute_value_id": res.product_attribute_value_id.id,
                            "qty": i,
                            "template_attri_value_id": res.id,
                        }
                    )
                """Used for Update Session Value and M2M in Product Varinat"""
                to_update = False
                value_qtyrecs = attribute_value_qty_obj.create(qty_list)
                for ptav_qty in res.ptav_product_variant_ids.product_attribute_value_qty_ids:
                    to_update = old_attribute_value_qty_ids.filtered(lambda l : l.id == ptav_qty.attribute_value_qty_id.id)
                    new_qty_recs = value_qtyrecs.filtered(lambda l:l.qty == to_update.qty)
                    product_session = self.env["product.config.session.value.qty"].search([("attribute_value_qty_id","=",ptav_qty.attribute_value_qty_id.id)])
                    if not new_qty_recs:
                        raise ValidationError(
                        _("You are not allowed to decrease the maximum quantity of the attribute value '{}' because it is associated with the product '{}' with quantity {}.".format(ptav_qty.attr_value_id.name,ptav_qty.product_id.display_name,to_update.qty))
                    )
                    product_session.write({"attribute_value_qty_id":new_qty_recs.id})
                    ptav_qty.write({"attribute_value_qty_id":new_qty_recs.id})
                old_attribute_value_qty_ids.unlink()
        return result
    def write(self, values):
        result = super().write(values)
        for res in self:
            if res.is_qty_required and (
                values.get("default_qty") or values.get("maximum_qty")
            ):
                qty_list = []
                attribute_value_qty_obj = self.env["attribute.value.qty"]
                for i in range(self.default_qty, self.maximum_qty + 1):
                    qty_list.append(
                        {
                            "product_tmpl_id": res.product_tmpl_id.id,
                            "product_attribute_id": res.attribute_id.id,
                            "product_attribute_value_id": res.product_attribute_value_id.id,
                            "qty": i,
                            "template_attri_value_id": res.id,
                        }
                    )
                res.attribute_value_qty_ids.unlink()
                attribute_value_qty_obj.create(qty_list)

        return result
