# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        digits="Product Cost Price",
    )

    weight = fields.Float(
        compute="_compute_weight_from_bom",
        store=True,
        help="Weight of the product variant. Computed from BOM components for "
             "configurable products, or inherited from template.",
    )

    @api.depends(
        "product_tmpl_id.weight",
        "bom_ids",
        "bom_ids.bom_line_ids",
        "bom_ids.bom_line_ids.product_id.weight",
        "bom_ids.bom_line_ids.product_qty",
    )
    def _compute_weight_from_bom(self):
        """
        Compute weight for product variants, especially configurable products.
        
        For configurable products (like HX500), weight is computed from:
        1. BOM components (sum of component weights * quantities)
        2. Parent template weight (if no BOM or BOM has no components)
        3. Direct weight field (if explicitly set on variant)
        
        This ensures weight is accessible in views and during shipping calculations.
        
        Note: This depends on 'bom_ids' which is provided by the 'mrp' module.
        If mrp is not installed, BOM-related dependencies will be ignored.
        """
        # Check if mrp module is available
        mrp_available = "mrp.bom" in self.env
        
        for product in self:
            weight = 0.0
            bom_weight_computed = False

            # Check if mrp module is installed and try to compute from BOM
            if mrp_available:
                try:
                    bom_obj = self.env["mrp.bom"]
                    # Try to find BOMs - check both phantom and normal types
                    # Check for phantom BOM first (common for configurable products)
                    bom = bom_obj._bom_find(
                        products=product, bom_type="phantom", company_id=product.company_id.id or False
                    )
                    if not bom or not bom.get(product):
                        # Fall back to normal BOM
                        bom = bom_obj._bom_find(
                            products=product, bom_type="normal", company_id=product.company_id.id or False
                        )
                    
                    if bom and bom.get(product):
                        bom_record = bom[product]
                        # Sum weights from BOM components
                        for line in bom_record.bom_line_ids:
                            component = line.product_id
                            component_weight = (
                                component.weight
                                or component.product_tmpl_id.weight
                                or 0.0
                            )
                            weight += component_weight * line.product_qty
                        bom_weight_computed = True
                except Exception:
                    # If BOM lookup fails, fall through to template weight
                    bom_weight_computed = False

            # If BOM weight was computed and is non-zero, use it
            if bom_weight_computed and weight > 0.0:
                product.weight = weight
            else:
                # Fall back to template weight
                if product.product_tmpl_id.weight:
                    product.weight = product.product_tmpl_id.weight
                else:
                    # Keep existing weight if set, otherwise 0
                    product.weight = product.weight or 0.0


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(
        digits="Product Cost Price",
    )
