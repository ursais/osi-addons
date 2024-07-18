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

                    # Archive the Variant's BoM
                    variant_bom.write({"active": False})
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

                    # Compare BOM lines
                    diff = False
                    bom_lines1 = variant_bom.bom_line_ids.sorted(
                        key=lambda x: x.product_id.id
                    )
                    bom_lines2 = new_variant_bom.bom_line_ids.sorted(
                        key=lambda x: x.product_id.id
                    )

                    if len(bom_lines1) != len(bom_lines2):
                        diff = True

                    for line1, line2 in zip(bom_lines1, bom_lines2):
                        if (
                            line1.product_id != line2.product_id
                            or line1.product_qty != line2.product_qty
                            or line1.operation_id != line2.operation_id
                        ):
                            diff = True

                    if not diff:
                        # Revert changes if no difference found
                        new_variant_bom.unlink()  # Delete the new BoM
                        variant_bom.write({"active": True})  # Activate the original BoM

    # END #########
