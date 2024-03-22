# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductConfiguratorSale(models.TransientModel):

    _name = "product.configurator.sale"
    _inherit = "product.configurator"
    _description = "Product Configurator Sale"

    order_id = fields.Many2one(comodel_name="sale.order", required=True, readonly=True)
    order_line_id = fields.Many2one(comodel_name="sale.order.line", readonly=True)

    domain_attr_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_values_sale_rel",
        "wiz_id",
        "attribute_id",
        string="Domain",
    )
    domain_attr_2_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_2_values_sale_rel",
        "wiz_id",
        "attribute_id",
        string="Domain",
    )

    def _get_order_line_vals(self, product_id):
        """Hook to allow custom line values to be put on the newly
        created or edited lines."""
        product = self.env["product.product"].browse(product_id)
        line_vals = {"product_id": product_id, "order_id": self.order_id.id}

        onchange_fields = ["price_unit", "product_uom", "tax_id"]
        line = self.env["sale.order.line"].new(line_vals)
        for field in onchange_fields:
            line_vals.update(
                {field: line._fields[field].convert_to_write(line[field], line)}
            )

        line_vals.update(
            {
                "config_session_id": self.config_session_id.id,
                "name": product._get_mako_tmpl_name(),
                "customer_lead": product.sale_delay,
            }
        )
        return line_vals

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super().action_config_done()
        if res.get("res_model") == self._name:
            return res
        model_name = "sale.order.line"
        line_vals = self._get_order_line_vals(res["res_id"])

        # Call onchange explicite as write and create
        # will not trigger onchange automatically
        order_line_obj = self.env[model_name]
        cfg_session = self.config_session_id
        fields_spec = cfg_session.get_onchange_specifications(model=model_name)
        fields_spec = {
            key: val
            for key, val in fields_spec.items()
            if key in list(line_vals.keys()) and key != "tax_id"
        }
        updates = order_line_obj.onchange(line_vals, ["product_id"], fields_spec)
        values = updates.get("value", {})
        values = cfg_session.get_vals_to_write(values=values, model=model_name)
        values.update(line_vals)

        if self.order_line_id:
            self.order_line_id.write(values)
        else:
            self.order_id.write({"order_line": [(0, 0, values)]})
        return

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get("default_order_line_id", False):
                sale_line = self.env["sale.order.line"].browse(
                    self.env.context["default_order_line_id"]
                )
                if sale_line.custom_value_ids:
                    vals["custom_value_ids"] = self._get_custom_values(
                        sale_line.config_session_id
                    )
        return super().create(vals_list)

    def _get_custom_values(self, session):
        custom_values = [(5,)] + [
            (
                0,
                0,
                {
                    "attribute_id": value_custom.attribute_id.id,
                    "value": value_custom.value,
                    "attachment_ids": [
                        (4, attach.id) for attach in value_custom.attachment_ids
                    ],
                },
            )
            for value_custom in session.custom_value_ids
        ]
        return custom_values
