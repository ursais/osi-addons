# Import Odoo libs
from odoo import api, fields, models


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    # COLUMNS ###
    remaining_price_subtotal = fields.Monetary(
        string="Remaining Subtotal",
        store=True,
    )
    remaining_price_total = fields.Monetary(
        string="Remaining Total",
        store=True,
    )
    remaining_price_tax = fields.Float(
        string="Remaining Tax",
        store=True,
    )

    # METHODS ###
    # END #######

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            line._compute_remaining_prices()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if any(
            key in vals
            for key in (
                "price_unit",
                "remaining_uom_qty",
                "taxes_id",
                "product_id",
                "currency_id",
                "order_id",
                "original_uom_qty",
                "ordered_uom_qty",
            )
        ):
            self._compute_remaining_prices()
        return res

    def _compute_remaining_prices(self):
        for line in self:
            partner = line.order_id.partner_id if line.order_id else None
            currency = line.currency_id or line.order_id.currency_id
            taxes = line.taxes_id.compute_all(
                line.price_unit,
                currency,
                line.remaining_uom_qty,
                product=line.product_id,
                partner=partner,
            )
            line.update(
                {
                    "remaining_price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "remaining_price_total": taxes["total_included"],
                    "remaining_price_subtotal": taxes["total_excluded"],
                }
            )

    # END #######
