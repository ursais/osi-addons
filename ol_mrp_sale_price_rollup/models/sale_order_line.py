# Import Odoo libs
from odoo import api, models


class SaleOrderLine(models.Model):
    """Inherit the sale order line to override method."""

    _inherit = "sale.order.line"

    # METHODS ##########

    @api.depends("product_id", "product_uom", "product_uom_qty")
    def _compute_price_unit(self):
        # Super `product_configurator_sale` to handle the
        # `config_session_id` condition cleanly
        super(SaleOrderLine, self)._compute_price_unit()

        for line in self:
            # Conditions from the core method
            if line.qty_invoiced > 0 or (
                line.product_id.expense_policy == "cost" and line.is_expense
            ):
                continue

            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
                continue

            # If Configuration Session then first set price to the
            # configuration sessions price which may include custom value
            # extra prices and such.
            if line.config_session_id:
                account_tax_obj = self.env["account.tax"]
                line.price_unit = account_tax_obj._fix_tax_included_price_company(
                    line.config_session_id.price,
                    line.product_id.taxes_id,
                    line.tax_id,
                    line.company_id,
                )

            # Retain core method logic to calculate `price_unit`
            # Pricelists Effects this price which is why we want this here.
            line = line.with_company(line.company_id)
            price = line._get_display_price()
            line.price_unit = line.product_id._get_tax_included_unit_price(
                line.company_id or line.env.company,
                line.order_id.currency_id,
                line.order_id.date_order,
                "sale",
                fiscal_position=line.order_id.fiscal_position_id,
                product_price_unit=price,
                product_currency=line.currency_id,
            )

    # END #########
