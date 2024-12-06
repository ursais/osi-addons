# Import Odoo libs
from odoo import api, fields, models
from odoo.addons.ol_base.tools import get_product_description


class SaleBlanketOrderLine(models.Model):
    """
    Add new fields to Sale blanket Order Line
    """

    _inherit = "sale.blanket.order.line"

    # COLUMNS #####

    customer_lead = fields.Float(
        compute="_compute_customer_lead",
        store=True,
        readonly=False,
        precompute=True,
    )
    product_state_id = fields.Many2one(
        "product.state",
        related="product_id.product_state_id",
    )
    discount = fields.Float(
        string="Discount (%)",
        compute="_compute_discount",
        digits="Discount",
        store=True,
        readonly=False,
        precompute=True,
    )
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
    currency_id = fields.Many2one(
        related="order_id.currency_id",
        depends=["order_id.currency_id"],
        store=True,
        precompute=True,
    )
    # M2M holding the values of product.attribute with create_variant field set to 'no_variant'
    # It allows keeping track of the extra_price associated to those attribute values and add them to the SO line description
    product_no_variant_attribute_value_ids = fields.Many2many(
        comodel_name="product.template.attribute.value",
        string="Extra Values",
        compute="_compute_no_variant_attribute_values",
        store=True,
        readonly=False,
        precompute=True,
        ondelete="restrict",
    )
    # END #########

    # METHODS #########
    @api.depends("product_id")
    def _compute_no_variant_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = (
                line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            )
            # remove the no_variant attributes that don't belong to this template
            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin not in valid_values:
                    line.product_no_variant_attribute_value_ids -= ptav

    def _get_product_price_context(self):
        """Gives the context for product price computation.

        :return: additional context to consider extra prices from attributes in the base product price.
        :rtype: dict
        """
        self.ensure_one()
        return self.product_id._get_product_price_context(
            self.product_no_variant_attribute_value_ids,
        )

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        price = self.pricelist_item_id._compute_price(
            product=self.product_id.with_context(**self._get_product_price_context()),
            quantity=self.original_uom_qty or 1.0,
            uom=self.product_uom,
            date=self.order_id.validity_date,
            currency=self.currency_id,
        )

        return price

    @api.depends("product_id", "product_uom", "original_uom_qty")
    def _compute_discount(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.discount = 0.0

            if not (
                line.order_id.pricelist_id
                and line.order_id.pricelist_id.discount_policy == "without_discount"
            ):
                continue

            line.discount = 0.0

            if not line.pricelist_item_id:
                # No pricelist rule was found for the product
                # therefore, the pricelist didn't apply any discount/change
                # to the existing sales price.
                continue

            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()

            if base_price != 0:  # Avoid division by zero
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (
                    discount < 0 and base_price < 0
                ):
                    # only show negative discounts if price is negative
                    # otherwise it's a surcharge which shouldn't be shown to the customer
                    line.discount = discount

    def _convert_to_sol_currency(self, amount, currency):
        """Convert the given amount from the given currency to the SO(L) currency.

        :param float amount: the amount to convert
        :param currency: currency in which the given amount is expressed
        :type currency: `res.currency` record
        :returns: converted amount
        :rtype: float
        """
        self.ensure_one()
        to_currency = self.currency_id or self.order_id.currency_id
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

    @api.depends("product_id", "company_id", "currency_id", "product_uom")
    def _compute_purchase_price(self):
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

    @api.depends("price_subtotal", "original_uom_qty", "purchase_price")
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (
                line.purchase_price * line.original_uom_qty
            )
            line.margin_percent = (
                line.price_subtotal and line.margin / line.price_subtotal
            )

    @api.depends(
        "original_uom_qty",
        "price_unit",
        "taxes_id",
        "order_id.partner_id",
        "product_id",
        "currency_id",
        "discount",
    )
    def _compute_amount(self):
        super()._compute_amount()
        for line in self:
            price = line.price_unit - (line.price_unit * line.discount) / 100
            taxes = line.taxes_id.compute_all(
                price,
                line.currency_id,
                line.original_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
            )
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    @api.model_create_multi
    def create(self, vals):
        """
        Override create method to include attribute values in the name
        of the record based on product attribute line settings.
        """
        res = super().create(vals)

        for rec in res:
            rec.name = get_product_description(rec.product_id)

        return res

    def write(self, vals):
        """
        Override write method to update record's name with attribute values
        based on changes in 'product_id' and attribute line settings.
        """
        res = super().write(vals)

        for rec in self:
            # If 'product_id' is being updated, adjust the record's description
            if vals.get("product_id"):
                product = rec.env["product.product"].browse(vals["product_id"])
                rec.name = get_product_description(product)

        return res

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        res = super().onchange_product()
        if self.env.context.get("update_pricelist"):
            self.price_unit = self._get_display_price()
            # self._compute_discount()
        return res

    # END ######
