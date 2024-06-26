# Copyright (C) 2024 - CURRENT, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model_create_multi
    def create(self, vals_list):
        """ReOrder BoM's."""
        # Create the BoM
        bom = super(MrpBom, self).create(vals_list)

        # Fetch all BoMs related to the product
        product_tmpl_id = bom.product_tmpl_id
        product_id = bom.product_id
        sequence = 1
        # Get the Variant BoM's (AKA have product_id set)
        if product_id:
            variant_boms = self.search(
                [
                    ("product_tmpl_id", "=", product_tmpl_id.id),
                    ("product_id", "!=", False),
                ]
            )
            if variant_boms:
                # Sort Variant BoMs by sequence
                sorted_variant_boms = variant_boms.sorted(key=lambda x: x.sequence)

                # Update sequences
                for vbom in sorted_variant_boms:
                    vbom.sequence = sequence
                    sequence += 1

        # Get the Master BoM's (AKA have product_id NOT set)
        if product_tmpl_id:
            master_boms = self.search(
                [
                    ("product_tmpl_id", "=", product_tmpl_id.id),
                    ("product_id", "=", False),
                ]
            )
            if master_boms:
                # Sort Master BoMs by sequence
                sorted_master_boms = master_boms.sorted(key=lambda x: x.sequence)

                for mbom in sorted_master_boms:
                    mbom.sequence = sequence
                    sequence += 1

        return bom
