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

    @api.depends("product_id", "company_id", "currency_id", "product_uom")
    def _compute_purchase_price(self):
        res = super()._compute_purchase_price()
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)

            # Convert the cost to the line UoM
            product_cost = line.product_id.uom_id._compute_price(
                line.product_id.total_cost,
                line.product_uom,
            )

            line.purchase_price = line._convert_to_sol_currency(
                product_cost, line.product_id.cost_currency_id
            )
        return res

    @api.model_create_multi
    def create(self,vals_list):
        res = super().create(vals_list)
        product_template = self.env["product.template"]
        for vals in vals_list:
            product_template_id = product_template.browse(vals.get("product_template_id"))
            is_bom_product_template = sum(product_template_id.mapped("bom_count")) > 0
            if not vals.get("config_session_id") and is_bom_product_template:
                product_template_id.button_bom_sale_price()
        return res

    # END #########
