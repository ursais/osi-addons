# Copyright (C) 2022-Today Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MRPBoM(models.Model):
    _inherit = "mrp.bom"

    bom_line_config_ids = fields.One2many(
        "mrp.bom.line.config", "bom_id", string="Configurable Components"
    )
    available_config_components = fields.Many2many(
        "product.template",
        compute="_compute_available_config_components",
        store=True,
    )

    @api.depends("bom_line_config_ids", "product_tmpl_id")
    def _compute_available_config_components(self):
        """Compute list of products available for configurable components"""
        for bom in self:
            if bom.config_ok and not bom.product_id:
                bom.available_config_components = False
                products = self.env["product.template"].search(
                    [
                        ("config_ok", "=", True),
                        ("id", "!=", bom.product_tmpl_id.id),
                        (
                            "id",
                            "!=",
                            bom.bom_line_config_ids.mapped("product_tmpl_id").ids,
                        ),
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
                                lambda m: m.attribute_id == attribute_line.attribute_id
                            )
                            bom_tmpl_values = bom.product_tmpl_id.mapped(
                                "attribute_line_ids.value_ids"
                            ).filtered(
                                lambda m: m.attribute_id == attribute_line.attribute_id
                            )
                            # If bom prod has all vals that conf comp has then add it
                            if all(att_val in bom_tmpl_values for att_val in prod_vals):
                                bom.available_config_components = [(4, prod.id)]


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    config_ok = fields.Boolean(related="product_id.config_ok")
    product_template_attribute_value_ids = fields.Many2many(
        related="product_id.product_template_attribute_value_ids"
    )
