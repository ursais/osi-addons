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
                    price=line.config_session_id.price,
                    prod_taxes=line.product_id.taxes_id,
                    line_taxes=line.tax_id,
                    company_id=line.company_id,
                )

            # Retain core method logic to calculate `price_unit`
            # Pricelists Effects this price which is why we want this here.
            line = line.with_company(line.company_id)
            price = line._get_display_price()
            line.price_unit = line.product_id._get_tax_included_unit_price(
                company=line.company_id or line.env.company,
                currency=line.order_id.currency_id,
                document_date=line.order_id.date_order,
                document_type="sale",
                is_refund_document=False,
                product_uom=None,
                product_currency=line.currency_id,
                product_price_unit=price,
                product_taxes=None,
                fiscal_position=line.order_id.fiscal_position_id,
            )

    # END #########
