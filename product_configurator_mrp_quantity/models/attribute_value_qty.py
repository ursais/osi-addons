import ast

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
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        query = super()._name_search(name, domain, operator, limit, order)
        domain = domain or []
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
            domain = [("product_tmpl_id", "=", wiz_id.product_tmpl_id.id)]
            if (
                qty_attr_id
                and wiz_id.dyn_qty_field_value == self._context.get("field_name")
                and wiz_id.domain_qty_ids
                and wiz_id.domain_qty_ids.mapped("product_attribute_id").id
                == int(qty_attr_id)
            ):
                domain = [("id", "in", wiz_id.domain_qty_ids.ids)]
            elif qty_attr_id and wiz_id.dyn_qty_field_value != self._context.get(
                "field_name"
            ):
                value_id = wiz_id.value_ids.filtered(
                    lambda val: val.attribute_id.id == int(qty_attr_id)
                )
                domains_dict = (
                    wiz_id.domains_dict and ast.literal_eval(wiz_id.domains_dict) or {}
                )
                context_value_id = self.browse(
                    domains_dict.get(self._context.get("field_name"))
                ).mapped("product_attribute_value_id")
                if domains_dict and context_value_id.id != value_id.id:
                    value_id = context_value_id
                domain_ids = self.search(
                    [
                        ("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),
                        ("product_attribute_value_id", "=", value_id.id),
                        ("product_attribute_id", "=", int(qty_attr_id)),
                    ]
                ).ids
                attribute_id = self._context.get("field_name").split(qty_field_prefix)
                if (
                    not domain_ids
                    and domains_dict
                    and self._context.get("field_name") in domains_dict
                ):
                    domain_ids = domains_dict[self._context.get("field_name")]
                elif (
                    self._context.get("field_name") not in domains_dict
                    and len(attribute_id) > 1
                ):
                    attribute_line_id = (
                        wiz_id.product_tmpl_id.attribute_line_ids.filtered(
                            lambda attr: attr.attribute_id.id == int(attribute_id[1])
                        )
                    )
                    value_id = attribute_line_id.default_val
                    domain_ids = self.search(
                        [
                            ("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),
                            ("product_attribute_value_id", "=", value_id.id),
                            ("product_attribute_id", "=", int(attribute_id[1])),
                        ]
                    ).ids
                domain = [("id", "in", domain_ids)]
            if name:
                if wiz_id.domain_qty_ids:
                    domain = [
                        ("qty", "ilike", int(name)),
                        ("id", "in", wiz_id.domain_qty_ids.ids),
                    ]
                else:
                    attribute_id = self._context.get("field_name").split(
                        qty_field_prefix
                    )

                    attribute_line_id = (
                        wiz_id.product_tmpl_id.attribute_line_ids.filtered(
                            lambda attr: attr.attribute_id.id == int(attribute_id[1])
                        )
                    )
                    value_id = attribute_line_id.default_val
                    domain_ids = self.search(
                        [
                            ("qty", "ilike", int(name)),
                            ("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),
                            ("product_attribute_id", "=", int(attribute_id[1])),
                            ("product_attribute_value_id", "=", value_id.id),
                        ]
                    )
                    domain = [("id", "in", domain_ids.ids)]

        return self._search(domain, limit=limit, order=order)

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
                domains_dict = (
                    wiz_id.domains_dict and ast.literal_eval(wiz_id.domains_dict) or {}
                )
                context_value_id = self.browse(
                    domains_dict.get(self._context.get("field_name"))
                ).mapped("product_attribute_value_id")
                if domains_dict and context_value_id.id != value_id.id:
                    value_id = context_value_id
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
