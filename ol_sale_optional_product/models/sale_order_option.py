# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrderOption(models.Model):
    """
    Adds margins to sale order options.
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

    # END #########
    # METHODS #####

    def _convert_to_sol_currency(self, amount, currency):
        """
        Helper method for computing purchase price. Same as on SO Line.
        Convert the given amount from the given currency to the SO(L) currency.

        :param float amount: the amount to convert
        :param currency: currency in which the given amount is expressed
        :type currency: `res.currency` record
        :returns: converted amount
        :rtype: float
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
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.order_id.company_id)

            # Convert the cost to the line UoM
            product_cost = line.product_id.uom_id._compute_price(
                line.product_id.standard_price,
                line.uom_id,
            )

            line.purchase_price = line._convert_to_sol_currency(
                product_cost, line.product_id.cost_currency_id
            )

    @api.depends(
        "uom_id",
        "purchase_price",
        "quantity",
    )
    def _compute_margin(self):
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
        """
        Compute the amounts of the SO Option line.
        """
        for line in self:
            if line.discount != 0.0:
                line.price_subtotal = (line.price_unit * line.quantity) * (
                    1 - (line.discount / 100)
                )
            else:
                line.price_subtotal = line.price_unit * line.quantity

    # END #########
