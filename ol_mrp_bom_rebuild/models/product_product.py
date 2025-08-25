# Import Odoo libs
from odoo import models


class ProductProduct(models.Model):
    """
    Inherit Product Variant, adding Rebuild Variant From BoM method.
    """

    _inherit = "product.product"

    # METHODS #####

    def _reset_variant_bom_with_scaffold_bom(self):
        """
        Reset a product variant's Bill of Materials (BoM) using a scaffold BoM
        (a BoM template). This leverages the configuration session logic to
        generate a new BoM based on the variant's configured values.

        Steps:
        - Find scaffold BoM (or fallback template BoM if no scaffold exists).
        - Locate existing variant-specific BoM(s).
            * If multiple exist, keep the latest and archive the rest.
            * If none exist, skip.
        - Use a configuration session to regenerate the BoM.
        - Compare old vs new BoM.
            * If different, keep the new one and increment version.
            * If identical, discard the new one and reactivate the old.
        """

        bom_obj = self.env["mrp.bom"]
        config_session_ = self.env["product.config.session"]

        for product in self:
            # Check if the product has variant values, is a product variant,
            # and is configurable
            if (
                product.product_template_variant_value_ids
                and product.is_product_variant
                and product.config_ok
            ):
                # Search for a scaffolding BoM for the product template
                scaffold_bom = bom_obj.search(
                    [
                        ("product_tmpl_id", "=", product.product_tmpl_id.id),
                        ("product_id", "=", False),
                        ("scaffolding_bom", "=", True),
                    ],
                    order="sequence",
                    limit=1,
                )

                # If no scaffolding BoM is found, search for a normal BoM
                # (with no variant)
                if not scaffold_bom:
                    scaffold_bom = bom_obj.search(
                        [
                            ("product_tmpl_id", "=", product.product_tmpl_id.id),
                            ("product_id", "=", False),
                            ("scaffolding_bom", "=", False),
                        ],
                        order="sequence",
                        limit=1,
                    )

                # If a scaffold BoM is found
                if scaffold_bom:
                    # Search for the existing variant-specific BoM
                    variant_bom = False
                    variant_boms = bom_obj.search(
                        [("product_id", "=", product.id)], order="id desc"
                    )

                    if variant_boms:
                        if len(variant_boms) > 1:
                            # Keep the latest, archive all others
                            latest_variant_bom = variant_boms[0]
                            (variant_boms - latest_variant_bom).write({"active": False})
                            variant_bom = latest_variant_bom
                        else:
                            variant_bom = variant_boms[0]

                    if not variant_bom:
                        # No existing variant BoM found — nothing to reset
                        continue

                    # Prepare to handle custom quantities for product attribute values
                    product_attribute_value_qty_ids = (
                        product.product_attribute_value_qty_ids
                    )
                    session_value_ids = (
                        scaffold_bom.bom_line_ids.config_set_id.configuration_ids.value_ids
                    )

                    # Filter configuration values based on the product's
                    # attribute value quantities
                    configuration_values = session_value_ids.filtered(
                        lambda value: value.id
                        in product.product_attribute_value_qty_ids.mapped(
                            "attr_value_id"
                        ).ids
                    )
                    filtered_value_qty_ids = product_attribute_value_qty_ids.filtered(
                        lambda value: value.attr_value_id.id in session_value_ids.ids
                    )

                    # Create a session quantity list to configure BoM lines
                    # with the correct quantities
                    session_qty_list = []
                    for value_qty in filtered_value_qty_ids:
                        session_qty_list.append(
                            (
                                0,
                                0,
                                {
                                    "product_attribute_id": value_qty.attr_value_id.attribute_id.id,
                                    "attr_value_id": value_qty.attr_value_id.id,
                                    "attribute_value_qty_id": value_qty.attribute_value_qty_id.id,
                                    "qty": value_qty.attribute_value_qty_id.qty,
                                },
                            )
                        )

                    # Temporarily deactivate the current variant's BoM before
                    # creating a new one
                    variant_bom.write({"active": False})

                    # Create a configuration session to generate
                    # a new BoM for the product variant
                    session = config_session_.with_context(
                        quantity_val_create=True
                    ).create_get_session(product.product_tmpl_id.id)

                    # Write product attribute values and custom quantities
                    # into the session
                    session.write(
                        {
                            "value_ids": [
                                (
                                    6,
                                    0,
                                    product.product_template_attribute_value_ids.mapped(
                                        "product_attribute_value_id"
                                    ).ids,
                                )
                            ],
                            "session_value_quantity_ids": session_qty_list,
                        }
                    )

                    # Confirm and finalize the session, which generates the new BoM
                    session.action_confirm()

                    # Delete the session (SQL to speed things up)
                    self.env.cr.execute(
                        "DELETE FROM product_config_session WHERE id=%s", (session.id,)
                    )

                    # Retrieve the newly created BoM
                    new_variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )

                    if new_variant_bom:
                        # Compare old and new BoMs
                        if self._compare_boms(variant_bom, new_variant_bom):
                            # Different → bump version and keep new
                            new_variant_bom.version = variant_bom.version + 1
                        else:
                            # Identical → discard new, reactivate old
                            self.env.cr.execute(
                                "DELETE FROM mrp_bom WHERE id=%s", (new_variant_bom.id,)
                            )
                            variant_bom.write({"active": True})

    def _compare_boms(self, bom1, bom2):
        """
        Compare two Bills of Materials (BoMs) and return True if they differ,
        otherwise return False.
        """

        # Sort the BoM lines by product ID for easier comparison
        bom_lines1 = bom1.bom_line_ids.sorted(key=lambda x: x.product_id.id)
        bom_lines2 = bom2.bom_line_ids.sorted(key=lambda x: x.product_id.id)

        # If the number of BoM lines is different, the BoMs are considered different
        if len(bom_lines1) != len(bom_lines2):
            return True

        # Compare each corresponding line in the two BoMs
        for line1, line2 in zip(bom_lines1, bom_lines2):
            # Check if product, quantity, or operation is different
            if (
                line1.product_id != line2.product_id
                or line1.product_qty != line2.product_qty
                or line1.operation_id != line2.operation_id
            ):
                return True

        # If all lines are identical, the BoMs are considered the same
        return False

    # END #########
