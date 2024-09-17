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
        Method to reset the variant's Bill of Materials (BoM) using a scaffold BoM
        (a BoM template) for product variants. We use the configuration session to
        do this as it contains all the logic to find and create the BoM based on
        the configured values and configuration sets on BoM lines.
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
                    variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )

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
                    session.unlink()

                    # Retrieve the newly created BoM
                    new_variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )

                    # Update the new BoM's version number
                    new_variant_bom.version = variant_bom.version + 1

                    # Compare the old and new BoMs to check for changes
                    if self._compare_boms(variant_bom, new_variant_bom):
                        # If the BoMs are different, keep the new one and
                        # deactivate the old one permanently
                        new_variant_bom.version = variant_bom.version + 1
                    else:
                        # If there are no differences, delete the new BoM and
                        # reactivate the original one
                        new_variant_bom.unlink()
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
