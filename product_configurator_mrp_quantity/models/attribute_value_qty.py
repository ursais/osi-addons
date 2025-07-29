import ast

from odoo import api, fields, models




class AttributeValueQty(models.Model):
    _name = "attribute.value.qty"
    _description = "A link between product attributes, value and the quantity"

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
        if self.env.context.get("wizard_id"):
            wiz_id = self.env[
                self.env.context.get("active_model", "product.configurator")
            ].browse(self.env.context.get("wizard_id"))
            qty_field_prefix = wiz_id._prefixes.get("qty_field")
            qty_attr_id  =False
            if self._context.get("field_name").startswith(qty_field_prefix):
                attr_qty_line = self._context.get("field_name").split(qty_field_prefix)[1]
                qty_attr_id = attr_qty_line.split("_")[1]
            # The values in `wiz_id.values_dict` will be set by the `get_form_vals` method from the `product_configurator_mrp_quantity` module.
            local_values_dict = wiz_id.values_dict and ast.literal_eval(wiz_id.values_dict) or {}
            for default_val in wiz_id.config_session_id.default_qty_ids:
                qty_attr_ids = self.search([("product_attribute_id","=",default_val.attribute_id.id),("product_tmpl_id","=",wiz_id.config_session_id.product_tmpl_id.id),("product_attribute_value_id","=",default_val.id)])
                qty_field_name = qty_field_prefix+str(default_val.attribute_id.id)
                if qty_field_name not in local_values_dict:
                    local_values_dict.update({qty_field_name:qty_attr_ids.ids})
            values_dict = local_values_dict
            domain = [("product_tmpl_id", "=", wiz_id.product_tmpl_id.id)]
            raw_value = values_dict.get(self._context.get("field_name"))
            if self._context.get("field_name") and values_dict.get(self._context.get("field_name")):
                if isinstance(raw_value, list):
                    value_ids = raw_value
                elif raw_value is not None:
                    value_ids = [raw_value]
                domain += [("id","in",value_ids)]
                if values_dict.get("preset_product",False) and value_ids is not None:
                    avq_data = self.browse(value_ids)
                    domain = [("product_tmpl_id", "=", wiz_id.product_tmpl_id.id),("template_attri_value_id","in",avq_data.mapped("template_attri_value_id").ids)]
                    print("@#####@@@@@@@@@@@@@@",domain)
            args = domain
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
