# Copyright (C) 2024 - CURRENT, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model
    def create(self, vals):
        if vals.get('product_id') and vals.get('product_tmpl_id'):
            # Find the minimum sequence among template-level BoMs for the same product template
            variant_boms = self.search([
                ('product_tmpl_id', '=', vals['product_tmpl_id']),
                ('product_id', '!=', False)
            ])
            if variant_boms:
                min_variant_seq = min(variant_boms.mapped('sequence'))
                vals['sequence'] = min_variant_seq - 1
            else:
                vals['sequence'] = 1  # Safe default if no template BoMs exist and also for master BoM
        res = super(MrpBom, self).create(vals)
        return res