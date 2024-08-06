from odoo import api, fields, models


class AttributeValueQty(models.Model):
    _name = "attribute.value.qty"

    name = fields.Char()
    product_tmpl_id = fields.Many2one("product.template", string="Product Template")
    product_attribute_id = fields.Many2one(
        "product.attribute", string="Product Attribute"
    )
    product_attribute_value_id = fields.Many2one(
        "product.attribute.value", string="Product Attribute Value"
    )
    qty = fields.Integer(string="Qty")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    template_attri_value_id = fields.Many2one("product.template.attribute.value")

    @api.depends("product_tmpl_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.qty}"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if self.env.context.get("wizard_id"):
            wiz_id = self.env[
                self.env.context.get("active_model", "product.configurator")
            ].browse(self.env.context.get("wizard_id"))
            qty_field_prefix = wiz_id._prefixes.get("qty_field")
            qty_attr_id = (
                self._context.get("field_name").startswith(qty_field_prefix)
                and self._context.get("field_name").split(qty_field_prefix)[1]
                or False
            )
            if (
                qty_attr_id
                and wiz_id.dyn_qty_field_value == self._context.get("field_name")
                and wiz_id.domain_qty_ids
            ):
                args = [("id", "in", wiz_id.domain_qty_ids.ids)]
            if qty_attr_id and wiz_id.dyn_qty_field_value != self._context.get(
                "field_name"
            ):
                value_id = wiz_id.value_ids.filtered(
                    lambda val: val.attribute_id.id == int(qty_attr_id)
                )
                domain_ids = self.search(
                    [
                        ("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),
                        ("product_attribute_value_id", "=", value_id.id),
                        ("product_attribute_id", "=", int(qty_attr_id)),
                    ]
                )
                args = [("id", "in", domain_ids.ids)]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def web_search_read(
        self, domain, specification, offset=0, limit=None, order=None, count_limit=None
    ):
        if self.env.context.get("wizard_id"):
            wiz_id = self.env["product.configurator"].browse(
                self.env.context.get("wizard_id")
            )
            qty_field_prefix = wiz_id._prefixes.get("qty_field")
            qty_attr_id = (
                self._context.get("field_name").startswith(qty_field_prefix)
                and self._context.get("field_name").split(qty_field_prefix)[1]
                or False
            )
            if (
                qty_attr_id
                and wiz_id.dyn_qty_field_value == self._context.get("field_name")
                and wiz_id.domain_qty_ids
            ):
                domain = [("id", "in", wiz_id.domain_qty_ids.ids)]
            if qty_attr_id and wiz_id.dyn_qty_field_value != self._context.get(
                "field_name"
            ):
                value_id = wiz_id.value_ids.filtered(
                    lambda val: val.attribute_id.id == int(qty_attr_id)
                )
                domain_ids = self.search(
                    [
                        ("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),
                        ("product_attribute_value_id", "=", value_id.id),
                        ("product_attribute_id", "=", int(qty_attr_id)),
                    ]
                )
                domain = [("id", "in", domain_ids.ids)]

        return super().web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )
