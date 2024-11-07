# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrderOption(models.Model):
    """
    Adds margins and subtotals to sale order optional products.
    """

    _inherit = "sale.order.option"

    # COLUMNS #####

    margin = fields.Float(
        "Margin",
        compute="_compute_margin",
        digits="Product Price",
        store=True,
        groups="base.group_user",
        precompute=True,
    )
    margin_percent = fields.Float(
        "Margin (%)",
        compute="_compute_margin",
        store=True,
        groups="base.group_user",
        precompute=True,
    )
    purchase_price = fields.Float(
        string="Cost",
        compute="_compute_purchase_price",
        digits="Product Price",
        store=True,
        readonly=False,
        copy=False,
        precompute=True,
        groups="base.group_user",
    )
    price_subtotal = fields.Float(
        string="Subtotal",
        compute="_compute_amount",
        store=True,
        precompute=True,
    )
    mrp_bom_id = fields.Many2one(
        "mrp.bom",
        string="BOM",
    )
    config_session_id = fields.Many2one(
        "product.config.session",
        string="Config session",
    )

    # END #########
    # METHODS #####

    def _convert_to_sol_currency(self, amount, currency):
        """
        Convert a given amount from the specified currency to the sale order
        line currency.

        This helper method is used for computing purchase prices by converting the given
        amount into the currency of the sale order line (SOL). If a currency conversion
        is required, it uses the sale order's date or the current date for
        the conversion.

        Args:
            amount (float): The amount to be converted.
            currency (res.currency): The currency in which the amount is
            currently expressed.

        Returns:
            float: The amount converted to the sale order line currency.
        """
        self.ensure_one()
        to_currency = self.order_id.currency_id
        if currency and to_currency and currency != to_currency:
            conversion_date = self.order_id.date_order or fields.Date.context_today(
                self
            )
            company = self.company_id or self.order_id.company_id or self.env.company
            return currency._convert(
                from_amount=amount,
                to_currency=to_currency,
                company=company,
                date=conversion_date,
                round=False,
            )
        return amount

    @api.depends(
        "product_id",
        "uom_id",
        "order_id.company_id",
        "order_id.currency_id",
    )
    def _compute_purchase_price(self):
        """
        Compute the purchase price for each line based on the product's standard price.

        This method checks if a product is assigned to the line. If so, it converts the
        product's cost to the line's unit of measure (UoM) and then converts it to the
        sale order line currency using `_convert_to_sol_currency`. The computed price
        is then stored in `purchase_price`.

        Sets:
            purchase_price (float): The computed purchase price for the sale order line.
        """
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.order_id.company_id)

            # Convert the product's standard price to the line UoM
            product_cost = line.product_id.uom_id._compute_price(
                line.product_id.standard_price,
                line.uom_id,
            )

            # Convert cost to the sale order line currency
            line.purchase_price = line._convert_to_sol_currency(
                product_cost, line.product_id.cost_currency_id
            )

    @api.depends(
        "uom_id",
        "purchase_price",
        "quantity",
    )
    def _compute_margin(self):
        # Compute the margins on the sale order optional product line
        for line in self:
            line.margin = line.price_subtotal - (line.purchase_price * line.quantity)
            line.margin_percent = (
                line.price_subtotal and line.margin / line.price_subtotal
            )

    @api.depends(
        "uom_id",
        "discount",
        "price_unit",
        "quantity",
    )
    def _compute_amount(self):
        # Calculate the subtotal amount for each sale order option line.
        for line in self:
            if line.discount != 0.0:
                line.price_subtotal = (line.price_unit * line.quantity) * (
                    1 - (line.discount / 100)
                )
            else:
                line.price_subtotal = line.price_unit * line.quantity

    # END #########
