# Copyright (C) 2022-Today Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def create_get_bom(self, variant, product_tmpl_id=None, values=None):
        if product_tmpl_id:
            master_bom = self.env["mrp.bom"].search(
                [
                    ("product_tmpl_id", "=", product_tmpl_id.id),
                    ("product_id", "=", False),
                ],
                order="sequence asc",
                limit=1,
            )
            vals = False
            wizard_values = variant.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            )
            for config_component_line in master_bom.bom_line_config_ids:
                config_component_vals = config_component_line.product_tmpl_id.mapped(
                    "attribute_line_ids.value_ids"
                )
                vals = set(wizard_values.ids).intersection(
                    set(config_component_vals.ids)
                )
                # Bypass config component variant creation if not all required vals are set
                do_not_create = False
                for line in config_component_line.product_tmpl_id.attribute_line_ids:
                    common_vals = set(vals) & set(line.value_ids.ids)
                    if line.required and not common_vals:
                        do_not_create = True
                if do_not_create:
                    continue

                # Otherwise create config component variant and bom
                else:
                    component_config_session = self.create_get_session(
                        config_component_line.product_tmpl_id.id
                    )
                    component_config_session.write({"value_ids": [(6, 0, vals)]})
                    component_config_session.action_confirm()
                    component_variant = component_config_session.product_id

                    # Look for existing configuration set and if doesn't exist, create it.
                    bom_line_config_set = self.env[
                        "mrp.bom.line.configuration.set"
                    ].search(
                        [("name", "=", component_variant.display_name)],
                        limit=1,
                    )
                    if not bom_line_config_set:
                        bom_line_config_set = self.env[
                            "mrp.bom.line.configuration.set"
                        ].create(
                            {
                                "name": component_variant.display_name,
                            }
                        )
                        self.env["mrp.bom.line.configuration"].create(
                            {
                                "config_set_id": bom_line_config_set.id,
                                "value_ids": [(6, 0, vals)],
                            }
                        )
                    # Look for existing bom line and if doesn't exist, create it.
                    existing_bom_line = self.env["mrp.bom.line"].search(
                        [
                            ("bom_id", "=", master_bom.id),
                            ("product_id", "=", component_config_session.product_id.id),
                            ("config_set_id", "=", bom_line_config_set.id),
                        ],
                        limit=1,
                    )
                    if not existing_bom_line:
                        self.env["mrp.bom.line"].create(
                            {
                                "bom_id": master_bom.id,
                                "product_id": component_variant.id,
                                "config_set_id": bom_line_config_set.id,
                                "product_qty": config_component_line.product_qty,
                            }
                        )
        return super().create_get_bom(variant, product_tmpl_id=None, values=None)
