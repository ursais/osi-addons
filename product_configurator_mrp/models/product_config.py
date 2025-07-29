# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def _get_parent_bom(self,product_tmpl_id):
        parent_bom = self.env["mrp.bom"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_id", "=", False),
                ("scaffolding_bom", "=", True),
            ],
            order="sequence asc",
            limit=1,
        )
        if not parent_bom:
            parent_bom = self.env["mrp.bom"].search(
                [
                    ("product_tmpl_id", "=", product_tmpl_id.id),
                    ("product_id", "=", False),
                ],
                order="sequence asc",
                limit=1,
            )

        return parent_bom


    def _get_bom_line(self, variant, product_tmpl_id):
        # Helping method to passing the BOM Line Vals.
        values = {}
        parent_bom = self._get_parent_bom(product_tmpl_id)
        if not parent_bom and self._context.get("product_id"):
            values = {"product_id": self._context.get("product_id").id, "product_qty": 1}

        elif parent_bom and self._context.get("parent_bom_line"):

            values = {
                "product_id": self._context.get("parent_bom_line").product_id.id,
                "product_qty": self._context.get("parent_bom_line").product_qty,
            }
        return values




    def create_get_bom(self, variant, product_tmpl_id=None, values=None):
        # default_type is set as 'product' when the user navigates
        # through menu item "Products". This conflicts
        # with the type for mrp.bom when mrpBom.onchange() is executed.
        ctx = self.env.context.copy()
        if ctx.get("default_type"):
            ctx.pop("default_type")
        self.env.context = ctx

        if values is None:
            values = {}
        if product_tmpl_id is None or variant.product_tmpl_id != product_tmpl_id:
            product_tmpl_id = variant.product_tmpl_id

        mrpBom = self.env["mrp.bom"]
        mrpBomLine = self.env["mrp.bom.line"]
        attr_products = variant.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id.product_id"
        )
        attr_values = variant.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id"
        )
        existing_bom = self.env["mrp.bom"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_id", "=", variant.id),
            ]
        )
        if existing_bom:
            return existing_bom[:1]

        parent_bom = self._get_parent_bom(product_tmpl_id)
        bom_type = parent_bom and parent_bom.type or "normal"
        bom_lines = []
        if not parent_bom:
            # If not Bom, then Cycle through attributes to add their
            # related products to the bom lines.
            for product in attr_products:
                bom_line_vals = self.with_context(product_id=product)._get_bom_line(variant,product_tmpl_id)
                specs = self.get_onchange_specifications(model="mrp.bom.line")
                for key, val in specs.items():
                    if val is None:
                        specs[key] = {}
                updates = mrpBomLine.onchange(
                    bom_line_vals, ["product_id", "product_qty"], specs
                )
                values = updates.get("value", {})
                values = self.get_vals_to_write(values=values, model="mrp.bom.line")
                values.update(bom_line_vals)
                bom_lines.append((0, 0, values))
        else:
            # If parent BOM is used, then look through Config Sets
            # on parent product's bom to add the products to the bom lines..
            session_value_ids = self.value_ids
            common_values_li = []
            for parent_bom_line in parent_bom.bom_line_ids:
                bom_line_value_ids = parent_bom_line.config_set_id.configuration_ids.value_ids
                common_values = next((value for value in bom_line_value_ids.ids if value in session_value_ids.ids), None)
                if parent_bom_line.config_set_id:
                    for config in parent_bom_line.config_set_id.configuration_ids:
                        # Add bom lines if config values are part of attr_values
                        if set(config.value_ids.ids).issubset(set(attr_values.ids)):
                            if parent_bom_line.bom_id.id == parent_bom.id:
                                print("?/////~~``~~~~~~~~~~~~~",parent_bom_line,common_values)
                                if common_values not in common_values_li:
                                    parent_bom_line_vals = self.with_context(parent_bom_line=parent_bom_line)._get_bom_line(variant,product_tmpl_id)
                                    specs = self.get_onchange_specifications(
                                        model="mrp.bom.line"
                                    )
                                    for key, val in specs.items():
                                        if val is None:
                                            specs[key] = {}
                                    updates = mrpBomLine.onchange(
                                        parent_bom_line_vals,
                                        ["product_id", "product_qty"],
                                        specs,
                                    )
                                    values = updates.get("value", {})
                                    values = self.get_vals_to_write(
                                        values=values, model="mrp.bom.line"
                                    )
                                    values.update(parent_bom_line_vals)
                                    bom_lines.append((0, 0, parent_bom_line_vals))
                    common_values_li.append(common_values)
                else:
                    parent_bom_line_vals = self.with_context(parent_bom_line=parent_bom_line)._get_bom_line(variant,product_tmpl_id)
                    specs = self.get_onchange_specifications(model="mrp.bom.line")
                    for key, val in specs.items():
                        if val is None:
                            specs[key] = {}
                    updates = mrpBomLine.onchange(
                        parent_bom_line_vals, ["product_id", "product_qty"], specs
                    )
                    values = updates.get("value", {})
                    values = self.get_vals_to_write(values=values, model="mrp.bom.line")
                    values.update(parent_bom_line_vals)
                    bom_lines.append((0, 0, values))
        if bom_lines:
            bom_values = {
                "product_tmpl_id": self.product_tmpl_id.id,
                "product_id": variant.id,
                "type": bom_type,
                "bom_line_ids": bom_lines,
            }
            specs = self.get_onchange_specifications(model="mrp.bom")
            for key, val in specs.items():
                if val is None:
                    specs[key] = {}
            updates = mrpBom.onchange(
                bom_values,
                [
                    "product_id",
                    "product_configurator_sale_mrproduct_tmpl_id",
                    "bom_line_ids",
                ],
                specs,
            )
            values = updates.get("value", {})
            values = self.get_vals_to_write(values=values, model="mrp.bom")
            values.update(bom_values)
            mrp_bom_id = mrpBom.sudo().create(values)
            if mrp_bom_id and parent_bom:
                if mrp_bom_id.company_id and not parent_bom.company_id:
                    mrp_bom_id.company_id = False
                for operation_line in parent_bom.operation_ids:
                    operation_line.copy(default={"bom_id": mrp_bom_id.id})
            return mrp_bom_id
        return False

    def create_get_variant(self, value_ids=None, custom_vals=None):
        variant = super().create_get_variant(
            value_ids=value_ids, custom_vals=custom_vals
        )
        self.create_get_bom(variant=variant, product_tmpl_id=self.product_tmpl_id)
        return variant
