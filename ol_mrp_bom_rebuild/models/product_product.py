from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _reset_variant_bom_with_master_bom(self):
        bom_obj = self.env["mrp.bom"]
        config_session_ = self.env["product.config.session"]
        for product in self:
            if product.is_product_variant and product.config_ok:
                master_bom = bom_obj.search(
                    [
                        ("product_tmpl_id", "=", product.product_tmpl_id.id),
                        ("product_id", "=", False),
                        ("scaffolding_bom", "=", False),
                    ],
                    order="sequence",
                    limit=1,
                )
                if master_bom:
                    variant_bom = bom_obj.search(
                        [("product_id", "=", product.id)], limit=1
                    )
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
