# Import Odoo libs
from odoo import api, fields, models
from collections import defaultdict


class SaleEstimateLineJob(models.Model):
    """
    Add customer_lead field Sale Estimate Line
    """

    _inherit = "sale.estimate.line.job"

    # COLUMNS #####

    customer_lead = fields.Float(
        compute="_compute_customer_lead",
        store=True,
        readonly=False,
        precompute=True,
    )
    margin = fields.Float(
        string="Margin",
        compute="_compute_margin",
        digits="Product Price",
        store=True,
    )
    margin_percent = fields.Float(
        string="Margin (%)",
        compute="_compute_margin",
        store=True,
    )
    purchase_price = fields.Float(
        string="Cost",
        compute="_compute_purchase_price",
        digits="Product Price",
        store=True,
        readonly=False,
        copy=False,
    )
    currency_id = fields.Many2one(
        related="estimate_id.currency_id",
        depends=["estimate_id.currency_id"],
        store=True,
        precompute=True,
    )
    product_type = fields.Selection(related="product_id.detailed_type")
    forecasted_issue = fields.Boolean(compute="_compute_forecasted_issue")
    virtual_available_at_date = fields.Float(
        compute="_compute_qty_at_date",
        digits="Product Unit of Measure",
    )
    scheduled_date = fields.Datetime(compute="_compute_qty_at_date")
    forecast_expected_date = fields.Datetime(compute="_compute_qty_at_date")
    free_qty_today = fields.Float(
        compute="_compute_qty_at_date",
        digits="Product Unit of Measure",
    )
    qty_available_today = fields.Float(compute="_compute_qty_at_date")
    display_qty_widget = fields.Boolean(compute="_compute_qty_to_deliver")
    estimate_state = fields.Selection(
        related="estimate_id.state",
        store=True,
        precompute=True,
        copy=False,
    )

    # END #########

    # METHODS #####

    @api.depends(
        "product_type",
        "product_uom_qty",
    )
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            if (
                line.estimate_state in ("draft", "sent", "confirm", "approve")
                and line.product_type == "product"
                and line.product_uom
                and line.product_uom_qty > 0
            ):
                line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    @api.depends(
        "product_id",
        "customer_lead",
        "product_uom_qty",
        "product_uom",
        "estimate_id.customer_request_date",
        "estimate_id.warehouse_id",
        "estimate_id.state",
    )
    def _compute_qty_at_date(self):
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env["sale.estimate.line.job"])
        treated = self.env["sale.estimate.line.job"]

        # Group lines by warehouse and requested date
        for line in self:
            if not (line.product_id and line.display_qty_widget):
                continue
            grouped_lines[
                (
                    line.estimate_id.warehouse_id.id,
                    line.estimate_id.customer_request_date,
                    line.estimate_id.state,
                )
            ] |= line

        # Compute quantities for each group
        for (warehouse, scheduled_date, estimate_state), lines in grouped_lines.items():
            product_qties = (
                lines.mapped("product_id")
                .with_context(to_date=scheduled_date, warehouse=warehouse)
                .read(["qty_available", "free_qty", "virtual_available"])
            )
            qties_per_product = {
                product["id"]: (
                    product["qty_available"],
                    product["free_qty"],
                    product["virtual_available"],
                )
                for product in product_qties
            }

            for line in lines:
                line.scheduled_date = scheduled_date
                line.estimate_state = estimate_state
                (
                    qty_available_today,
                    free_qty_today,
                    virtual_available_at_date,
                ) = qties_per_product[line.product_id.id]
                line.qty_available_today = (
                    qty_available_today - qty_processed_per_product[line.product_id.id]
                )
                line.free_qty_today = (
                    free_qty_today - qty_processed_per_product[line.product_id.id]
                )
                line.virtual_available_at_date = (
                    virtual_available_at_date
                    - qty_processed_per_product[line.product_id.id]
                )
                line.forecast_expected_date = False

                product_qty = line.product_uom_qty
                if (
                    line.product_uom
                    and line.product_id.uom_id
                    and line.product_uom != line.product_id.uom_id
                ):
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(
                        line.qty_available_today, line.product_uom
                    )
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(
                        line.free_qty_today, line.product_uom
                    )
                    line.virtual_available_at_date = (
                        line.product_id.uom_id._compute_quantity(
                            line.virtual_available_at_date, line.product_uom
                        )
                    )
                    product_qty = line.product_uom._compute_quantity(
                        product_qty, line.product_id.uom_id
                    )

                qty_processed_per_product[line.product_id.id] += product_qty

            treated |= lines

        # Remaining lines
        remaining = self - treated
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False

    @api.depends("product_uom_qty", "product_id")
    def _compute_forecasted_issue(self):
        for line in self:
            warehouse = line.estimate_id.warehouse_id
            line.forecasted_issue = False
            if line.product_id:
                virtual_available = line.product_id.with_context(
                    warehouse=warehouse.id,
                ).virtual_available
                if virtual_available <= 0:
                    line.forecasted_issue = True

    def action_product_forecast_report(self):
        self.ensure_one()
        action = self.product_id.action_product_forecast_report()
        action["context"] = {
            "active_id": self.product_id.id,
            "active_model": "product.product",
        }
        warehouse = self.estimate_id.warehouse_id
        if warehouse:
            action["context"]["warehouse"] = warehouse.id
        return action

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay or 0.0

    @api.depends(
        "product_id",
        "company_id",
        "currency_id",
        "product_uom",
    )
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)

            # Convert the cost to the line UoM
            product_cost = line.product_id.uom_id._compute_price(
                line.product_id.product_tmpl_id.approved_total_cost,
                line.product_uom,
            )

            line.purchase_price = line._convert_to_sol_currency(
                product_cost, line.product_id.cost_currency_id
            )

    @api.depends("price_subtotal", "product_uom_qty", "purchase_price")
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (
                line.purchase_price * line.product_uom_qty
            )
            line.margin_percent = (
                line.price_subtotal and line.margin / line.price_subtotal
            )

    def _convert_to_sol_currency(self, amount, currency):
        """Convert the given amount from the given currency to the SO(L) currency.

        :param float amount: the amount to convert
        :param currency: currency in which the given amount is expressed
        :type currency: `res.currency` record
        :returns: converted amount
        :rtype: float
        """
        self.ensure_one()
        to_currency = self.currency_id or self.estimate_id.currency_id
        if currency and to_currency and currency != to_currency:
            conversion_date = (
                self.estimate_id.estimate_date or fields.Date.context_today(self)
            )
            company = self.company_id or self.estimate_id.company_id or self.env.company
            return currency._convert(
                from_amount=amount,
                to_currency=to_currency,
                company=company,
                date=conversion_date,
                round=False,
            )
        return amount

    # END #########
