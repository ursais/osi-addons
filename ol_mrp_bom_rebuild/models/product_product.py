# Import Odoo libs
from odoo import models


class ProductProduct(models.Model):
    """
    Inherit Product Variant, adding Rebuild Variant From BoM method.
    """

    _inherit = "product.product"

    # METHODS #####

    def _reset_variant_bom_with_scaffold_bom(self):
        """method to reset variant BoM with scaffold BoM for product variants"""
        bom_obj = self.env["mrp.bom"]
        config_session_ = self.env["product.config.session"]

        for product in self:
            if (
                product.product_template_variant_value_ids
                and product.is_product_variant
                and product.config_ok
            ):
                # Find the scaffolding bom
                scaffold_bom = bom_obj.search(
                    [
                        ("product_tmpl_id", "=", product.product_tmpl_id.id),
                        ("product_id", "=", False),
                        ("scaffolding_bom", "=", True),
                    ],
                    order="sequence",
                    limit=1,
                )
                # If no BoM found that has scaffolding true, then search for
                # BoM without a variant which would then be considered
                # the scaffolding BoM.
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
                if scaffold_bom:
                    # Find the variant's BoM
                    variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )

                    # Temporarily deactivate the variant's BoM
                    variant_bom.write({"active": False})

                    # Create a temporary session to generate a new BoM without committing
                    session = config_session_.create_get_session(
                        product.product_tmpl_id.id
                    )
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
                            ]
                        }
                    )
                    session.action_confirm()
                    session.unlink()

                    new_variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )
                    new_variant_bom.version = variant_bom.version + 1

                    # Compare BOM lines before committing changes
                    if self._compare_boms(variant_bom, new_variant_bom):
                        # Keep the new BoM and deactivate the old one permanently
                        new_variant_bom.version = variant_bom.version + 1
                    else:
                        # Revert changes if no difference found
                        new_variant_bom.unlink()  # Delete the new BoM
                        variant_bom.write(
                            {"active": True}
                        )  # Reactivate the original BoM

    def _compare_boms(self, bom1, bom2):
        """Compare two Bills of Materials (BoMs) and return True if they are different,
        False otherwise."""

        # Sort BoM lines by product ID for both BoMs
        bom_lines1 = bom1.bom_line_ids.sorted(key=lambda x: x.product_id.id)
        bom_lines2 = bom2.bom_line_ids.sorted(key=lambda x: x.product_id.id)

        # If the number of lines in both BoMs is different, they are different
        if len(bom_lines1) != len(bom_lines2):
            return True

        # Compare each corresponding line in both BoMs
        for line1, line2 in zip(bom_lines1, bom_lines2):
            # Check if product, quantity, or operation differs
            if (
                line1.product_id != line2.product_id
                or line1.product_qty != line2.product_qty
                or line1.operation_id != line2.operation_id
            ):
                return True

        # If all lines are identical, the BoMs are the same
        return False

    # END #########
