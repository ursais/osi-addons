# Import Odoo libs
from odoo import api, models


class MRPBom(models.Model):
    """Inherit BoM to override compute method, adding context to speed up migration."""

    _inherit = "mrp.bom"

    @api.depends("bom_line_config_ids", "product_tmpl_id")
    def _compute_available_config_components(self):
        """
        Compute list of products available for configurable components

        Override to optimize performance during data migration by reducing unnecessary loops.
        This method only processes records where `system_tier` is 'normal'. For all other
        `system_tier` values, `available_config_components` is immediately set to False.

        This override is specifically designed to support Script 6 execution, which is triggered
        via Server Action 2. A context key `is_data_migration` is expected to be present during migration
        to identify when this logic should run."""
        for bom in self:
            if (
                self._context.get("is_data_migration")
                and bom.config_ok
                and not bom.product_id
            ):
                bom.available_config_components = False
                if bom.product_tmpl_id.system_tier == "normal":
                    products = self.env["product.template"].search(
                        [
                            ("config_ok", "=", True),
                            ("id", "!=", bom.product_tmpl_id.id),
                            (
                                "id",
                                "!=",
                                bom.bom_line_config_ids.mapped("product_tmpl_id").ids,
                            ),
                            ("system_tier", "=", "normal"),
                        ]
                    )
                    for prod in products:
                        prod_attrs = prod.mapped("attribute_line_ids.attribute_id")
                        bom_tmpl_attrs = bom.product_tmpl_id.mapped(
                            "attribute_line_ids.attribute_id"
                        )
                        # First compare that bom prod contains all attr that conf comp has
                        if all(attr in bom_tmpl_attrs for attr in prod_attrs):
                            for attribute_line in prod.attribute_line_ids:
                                prod_vals = prod.mapped(
                                    "attribute_line_ids.value_ids"
                                ).filtered(
                                    lambda m, attribute_line=attribute_line: m.attribute_id
                                    == attribute_line.attribute_id
                                )
                                bom_tmpl_values = bom.product_tmpl_id.mapped(
                                    "attribute_line_ids.value_ids"
                                ).filtered(
                                    lambda m, attribute_line=attribute_line: m.attribute_id
                                    == attribute_line.attribute_id
                                )
                                # If bom prod has all vals that conf comp has then add it
                                if all(
                                    att_val in bom_tmpl_values for att_val in prod_vals
                                ):
                                    bom.available_config_components = [(4, prod.id)]
            else:
                return super()._compute_available_config_components
