# Copyright (C) 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _search(
        self,
        domain,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
    ):
        ctx = dict(self._context)
        if not domain:
            domain = []
        if ctx.get("bom_id") and ctx.get("product_id"):
            product_lst = []
            mrp_bom_id = (
                self.env["mrp.bom"].sudo().search([("id", "=", ctx.get("bom_id"))])
            )
            line_ids = mrp_bom_id.bom_line_ids.filtered(
                lambda x: x.product_id.id == ctx.get("product_id")
            )
            for line in line_ids:
                product_lst += line.substitute_product_ids.ids
            if product_lst:
                domain += [("id", "in", product_lst)]

        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid,
        )
