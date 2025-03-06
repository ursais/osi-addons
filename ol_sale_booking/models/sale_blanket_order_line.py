# Import Odoo libs
from odoo import fields, models, api


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    # COLUMNS ###
    remaining_price_subtotal = fields.Monetary(
        compute="_compute_remaining_amount",
        string="Remaining Subtotal",
        store=True,
    )
    remaining_price_total = fields.Monetary(
        compute="_compute_remaining_amount",
        string="Remaining Total",
        store=True,
    )
    remaining_price_tax = fields.Float(
        compute="_compute_remaining_amount",
        string="Remaining Tax",
        store=True,
    )

    # METHODS ###
    # END #######

    @api.depends(
        "remaining_uom_qty",
        "price_unit",
        "taxes_id",
        "order_id.partner_id",
        "product_id",
        "currency_id",
    )
    def _compute_remaining_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.taxes_id.compute_all(
                price,
                line.currency_id,
                line.remaining_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
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
