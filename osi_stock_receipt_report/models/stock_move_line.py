# Copyright (C) 2026 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    supplier_lot = fields.Char(
        string="Supplier Lot",
        help="Lot or batch number as provided by the supplier.",
    )

    def _get_supplier_product_name(self):
        """Return the vendor's product name for the move line's supplier.

        Looks up the product.supplierinfo matching the picking's partner
        (commercial entity) and returns the vendor product name if found.
        """
        self.ensure_one()
        partner = self.picking_id.partner_id.commercial_partner_id
        if not partner:
            return ""
        supplierinfo = self.product_id.seller_ids.filtered(
            lambda s: s.partner_id == partner
        )[:1]
        return supplierinfo.product_name or ""

    def _get_supplier_product_code(self):
        """Return the vendor's product code for the move line's supplier."""
        self.ensure_one()
        partner = self.picking_id.partner_id.commercial_partner_id
        if not partner:
            return ""
        supplierinfo = self.product_id.seller_ids.filtered(
            lambda s: s.partner_id == partner
        )[:1]
        return supplierinfo.product_code or ""
