# Import Odoo libs
from odoo import fields, api, models
from odoo.exceptions import ValidationError


class ProductPriceReview(models.Model):
    """
    The pricing review is used to review and pricing changes and once approved,
     apply those pricing changes to the product.
    """

    _name = "product.price.review"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Manages and keep record and track the changes in product price."

    # COLUMNS ##########

    # General fields on Price Review
    name = fields.Char(
        string="Price Adjustment", required=True, readonly=True, default="New..."
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="[('has_configurable_attributes','=',False)]",
    )
    default_code = fields.Char(related="product_id.default_code")
    detailed_type = fields.Selection(related="product_id.detailed_type")
    categ_id = fields.Many2one(
        "product.category",
        string="Product Category",
        related="product_id.categ_id",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    state = fields.Selection(
        [
            ("new", "Draft"),
            ("in_progress", "In Progress"),
            ("reject", "Rejected"),
            ("validated", "Validated"),
        ],
        default="new",
        string="State",
    )
    user_id = fields.Many2one("res.users", string="Assigned To")
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
    )

    # Origin fields, recorded on the price review for historical purposes
    origin_last_purchase_currency_id = fields.Many2one("res.currency")
    origin_last_purchase_price = fields.Float(
        string="Original Last PO Cost",
        help="Product cost on most recent confirmed purchase",
    )
    origin_last_purchase_price_converted = fields.Float(
        string="Original Last PO Cost (Currency Converted)",
        store=True,
        compute="_compute_origin_last_purchase_price_converted",
        help="Product cost on most recent confirmed purchase",
    )
    origin_tariff_percent = fields.Float(string="Original Tariff Percent")
    origin_tooling_cost = fields.Float(string="Original Tooling Cost")
    origin_defrayment_cost = fields.Float(
        string="Original Defrayment Cost",
    )
    origin_carrier_multiplier_id = fields.Many2one(
        "delivery.carrier.multiplier",
        string="Original Inbound Shipping Method",
    )
    origin_default_shipping_cost = fields.Float(
        string="Original Default Shipping Cost",
    )
    origin_total_cost = fields.Float(
        string="Original Total Cost",
        help="Total cost of product including purchase cost, tariff,"
        " tooling, defrayment, and shipping.",
    )
    origin_last_purchase_margin = fields.Float(
        string="Original Last PO Margin",
        compute="_compute_last_purchase_margin",
        store=True,
    )
    origin_suggested_margin = fields.Float(
        string="Original Suggested Margin",
        help="Default margin if no other pricing methods are set.",
    )
    origin_override_margin = fields.Float(
        string="Original Override Margin",
        help="Desired margin for pricing.",
    )
    origin_charm_price = fields.Selection(
        selection=[
            ("none", "None (No rounding)"),
            (".00", "Round to nearest dollar"),
            (".95", "Round to nearest .95 cents"),
            (".99", "Round to nearest .99 cents"),
        ],
        default="none",
        help="Modifies the final price based on charm price:"
        "None: No change is made to the final price."
        ".00: Rounds the price to the nearest dollar."
        ".95: Rounds the price to the nearest .95 cents."
        ".99: Rounds the price to the nearest .99 cents.",
    )
    origin_override_price = fields.Float(
        string="Original Override Price",
        help="Fixed price for product that overrides margin pricing.",
    )
    origin_special_price = fields.Float(
        string="Original Special Price",
        help="Special fixed price that overrides all other pricing selections."
        " Original price shows with strikethrough text on e-commerce platform",
    )
    origin_vendor_id = fields.Many2one(
        "res.partner",
        string="Original Vendor",
        help="Vendor from which the purchased component triggered a price review.",
    )
    origin_purchase_line_id = fields.Many2one(
        "purchase.order.line",
        string="Original Purchase Order",
        help="Purchase Order that triggered a price review.",
    )
    origin_purchase_id = fields.Many2one(
        "purchase.order",
        string="Original Purchase Order",
        help="Purchase Order that triggered a price review.",
    )

    # Current Pricing Summary Fields
    origin_final_price = fields.Float(
        string="Original Final Price",
    )
    origin_based_on = fields.Char(
        string="Original Based On",
    )
    origin_margin = fields.Float(
        string="Original Margin",
        compute="_compute_origin_margins",
        store=True,
    )
    origin_margin_percent = fields.Float(
        string="Original Margin %",
        compute="_compute_origin_margins",
        store=True,
    )

    # Fields that can be adjusted to update the price of the product
    tooling_cost = fields.Float(
        string="Tooling Cost",
        help="Non-recurring engineering costs.",
    )
    defrayment_cost = fields.Float(
        string="Defrayment Cost",
        help="Project costs to be recouped over the lifecycle of the product.",
    )
    carrier_multiplier_id = fields.Many2one(
        "delivery.carrier.multiplier",
        string="Inbound Shipping Method",
        help="Inbound shipping method to be used for estimating shipping costs.",
    )
    default_shipping_cost = fields.Float(
        string="Default Shipping Cost",
        compute="_compute_default_shipping_cost",
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost",
        help="Total cost of product including purchase cost, tariff,"
        " tooling, defrayment, and shipping.",
    )
    suggested_margin = fields.Float(
        related="categ_id.suggested_margin",
        string="Suggested Margin",
    )
    cost_delta = fields.Float(
        string="Cost Delta",
        store=True,
        compute="_compute_cost_delta",
        help="Original Total Cost - Price Review Total Cost",
    )

    # New Pricing Summary Fields
    final_price = fields.Float(
        string="Final Price", compute="_compute_final_price", store=True
    )
    based_on = fields.Char(string="Based On", compute="_compute_based_on")
    margin = fields.Float(string="Margin", compute="_compute_margins")
    margin_percent = fields.Float(string="Margin %", compute="_compute_margins")
    tariff_percent = fields.Float(
        string="Tariff Percent",
        help="Percentage markup of cost to include tariffs.",
    )
    override_margin = fields.Float(
        string="Override Margin",
        help="Desired margin for pricing.",
    )
    charm_price = fields.Selection(
        selection=[
            ("none", "None (No rounding)"),
            (".00", "Round to nearest dollar"),
            (".95", "Round to nearest .95 cents"),
            (".99", "Round to nearest .99 cents"),
        ],
        default="none",
        help="Modifies the final price based on charm price:"
        "None: No change is made to the final price."
        ".00: Rounds the price to the nearest dollar."
        ".95: Rounds the price to the nearest .95 cents."
        ".99: Rounds the price to the nearest .99 cents.",
    )
    override_price = fields.Float(
        string="Override Price",
        help="Fixed price for product that overrides margin pricing.",
    )
    special_price = fields.Float(
        string="Special Price",
        help="Special fixed price that overrides all other pricing selections."
        " Original price shows with strikethrough text on e-commerce platform",
    )
    calculated_price = fields.Float(
        string="Calculated Price",
        compute="_compute_calculated_price",
        help="Price calculation based on Suggested and Override Margin fields set.",
    )

    # END ##########
    # METHODS ##########

    # ONCHANGE METHODS
    @api.onchange("product_id")
    def onchange_product_id(self):
        """Update fields based on selected product for historical documentation."""
        for rec in self:
            if rec.product_id:
                product = rec.product_id.with_company(rec.company_id)

                # Populate historical fields on price review
                rec.origin_final_price = product.list_price
                rec.origin_purchase_line_id = product.last_purchase_line_id.id
                rec.origin_vendor_id = (
                    product.last_purchase_line_id.order_id.partner_id.id
                )
                rec.origin_purchase_id = product.last_purchase_line_id.order_id.id
                rec.origin_last_purchase_price = (
                    product.last_purchase_line_id.price_unit
                )
                rec.origin_last_purchase_currency_id = (
                    product.last_purchase_line_id.order_id.currency_id
                )
                rec.origin_tariff_percent = product.tariff_percent
                rec.origin_tooling_cost = product.tooling_cost
                rec.origin_defrayment_cost = product.defrayment_cost
                rec.origin_carrier_multiplier_id = product.carrier_multiplier_id
                rec.origin_default_shipping_cost = product.default_shipping_cost
                rec.origin_total_cost = product.total_cost
                rec.origin_suggested_margin = product.suggested_margin
                rec.origin_override_margin = product.override_margin
                rec.origin_override_price = product.override_price
                rec.origin_special_price = product.special_price
                rec.origin_based_on = product.based_on

                if product.charm_price:
                    rec.origin_charm_price = product.charm_price
                else:
                    rec.origin_charm_price = "none"

                # Populate proposed pricing fields so user doesn't have to reset them.
                rec.tariff_percent = product.tariff_percent
                rec.tooling_cost = product.tooling_cost
                rec.defrayment_cost = product.defrayment_cost
                rec.carrier_multiplier_id = product.carrier_multiplier_id
                rec.override_margin = product.override_margin
                rec.charm_price = product.charm_price
                rec.override_price = product.override_price
                rec.special_price = product.special_price
                rec.based_on = product.based_on

    @api.onchange("user_id")
    def onchange_user_id(self):
        """Update state to 'in_progress' when user_id is assigned and state is 'new'."""
        for rec in self:
            if rec.user_id and rec.state == "new":
                rec.state = "in_progress"

    # COMPUTE METHODS
    @api.depends(
        "carrier_multiplier_id",
        "product_id.weight",
    )
    def _compute_default_shipping_cost(self):
        """Compute default shipping cost based on carrier multiplier
        and product weight."""
        default_shipping_cost = 0.0
        for rec in self:
            if rec.carrier_multiplier_id:
                default_shipping_cost = (
                    rec.product_id.weight * rec.carrier_multiplier_id.multiplier
                )
            rec.default_shipping_cost = default_shipping_cost

    @api.depends("origin_last_purchase_price")
    def _compute_origin_last_purchase_price_converted(self):
        """
        Compute the converted last purchase price based on the origin currency.
        If the origin currency differs from the company's currency, convert the price.
        Otherwise, use the origin last purchase price directly.
        """
        for rec in self:
            if (
                rec.origin_last_purchase_currency_id
                and rec.origin_last_purchase_currency_id != self.env.company.currency_id
            ):
                rec.origin_last_purchase_price_converted = (
                    rec.origin_last_purchase_currency_id._convert(
                        rec.origin_last_purchase_price, rec.company_id.currency_id
                    )
                )
            else:
                rec.origin_last_purchase_price_converted = (
                    rec.origin_last_purchase_price
                )

    @api.depends(
        "origin_final_price",
        "origin_last_purchase_price",
        "origin_tariff_percent",
        "origin_tooling_cost",
        "origin_defrayment_cost",
        "origin_default_shipping_cost",
    )
    def _compute_last_purchase_margin(self):
        """
        Compute the last purchase margin as a percentage.
        The margin is calculated based on the list price, converted last purchase price,
        tariff, tooling cost, defrayment cost, and default shipping cost.
        """
        for rec in self:
            last_purchase_margin = 0
            if rec.product_id.list_price:
                last_purchase_margin = (
                    rec.product_id.list_price
                    - (
                        rec.origin_last_purchase_price_converted
                        * (1 + rec.origin_tariff_percent)
                    )
                    + rec.origin_tooling_cost
                    + rec.origin_defrayment_cost
                    + rec.origin_default_shipping_cost
                ) / rec.product_id.list_price
        self.origin_last_purchase_margin = last_purchase_margin

    @api.depends(
        "origin_final_price",
        "origin_total_cost",
    )
    def _compute_origin_margins(self):
        """
        Compute the origin margins.
        The margin is calculated as the difference between the final price and the
        total cost. The margin percentage is the margin divided by the final price.
        """
        for rec in self:
            origin_margin = 0.0
            origin_margin_percent = 0
            if rec.origin_final_price:
                origin_margin = rec.origin_final_price - rec.origin_total_cost
                if rec.origin_margin:
                    origin_margin_percent = rec.origin_margin / rec.origin_final_price
            rec.origin_margin = origin_margin
            rec.origin_margin_percent = origin_margin_percent

    @api.depends(
        "origin_last_purchase_price",
        "tariff_percent",
        "tooling_cost",
        "defrayment_cost",
        "default_shipping_cost",
    )
    def _compute_total_cost(self):
        """
        Compute the total cost by summing up the converted last purchase price with
        tariff, tooling cost, defrayment cost, and default shipping cost.
        """
        for rec in self:
            rec.total_cost = (
                rec.origin_last_purchase_price_converted * (1 + rec.tariff_percent)
                + rec.tooling_cost
                + rec.defrayment_cost
                + rec.default_shipping_cost
            )

    @api.depends(
        "total_cost",
        "origin_total_cost",
    )
    def _compute_cost_delta(self):
        """
        Compute the cost delta, which is the difference between the origin total cost
        and the current total cost.
        """
        for rec in self:
            cost_delta = 0.0
            if rec.total_cost:
                cost_delta = rec.origin_total_cost - rec.total_cost
            rec.cost_delta = cost_delta

    @api.depends(
        "override_margin",
        "total_cost",
    )
    def _compute_calculated_price(self):
        """
        Compute the calculated price based on the total cost and margins.
        Raises a validation error if the suggested or override margin is 100%.
        If an override margin is provided, it is used for the calculation.
        Otherwise, the suggested margin is used.
        """
        for rec in self:
            if rec.suggested_margin == 1.0:
                raise ValidationError("The suggested margin cannot be 100%")
            if rec.override_margin == 1.0:
                raise ValidationError("The override margin cannot be 100%")

            if rec.override_margin == 0.0 and rec.suggested_margin < 1.0:
                rec.calculated_price = rec.total_cost / ((1 - rec.suggested_margin) / 1)
            elif rec.override_margin < 1.0:
                rec.calculated_price = rec.total_cost / ((1 - rec.override_margin) / 1)
            else:
                rec.calculated_price = rec.total_cost

    @api.depends(
        "tariff_percent",
        "tooling_cost",
        "defrayment_cost",
        "carrier_multiplier_id",
        "special_price",
        "override_price",
        "margin",
        "calculated_price",
        "charm_price",
    )
    def _compute_final_price(self):
        """Compute the final price based on various factors."""
        for rec in self:
            final_price = 0

            # Determine final price based on special/override price or calculated price
            if rec.special_price:
                final_price = rec.special_price
            elif rec.override_price:
                final_price = rec.override_price
            else:
                final_price = rec.calculated_price

                # Apply Charm Pricing if specified
                if rec.charm_price == ".00":
                    final_price = round(final_price)  # Round to nearest .00
                elif rec.charm_price == ".95":
                    final_price = round(final_price) - 0.05  # Round to nearest .95
                elif rec.charm_price == ".99":
                    final_price = round(final_price) - 0.01  # Round to nearest .99
                else:
                    final_price = final_price

            # Assign computed final price to the record
            rec.final_price = final_price

    @api.depends("final_price", "total_cost")
    def _compute_margins(self):
        """Compute margins based on final price and total cost."""

        for rec in self:
            margin = 0
            margin_percent = 0

            # Calculate margin and margin percentage if final price is defined
            if rec.final_price:
                margin = rec.final_price - rec.total_cost
                margin_percent = margin / rec.final_price

            # Assign computed margin and margin percentage to the record
            rec.margin = margin
            rec.margin_percent = margin_percent

    @api.depends(
        "final_price",
        "total_cost",
        "override_margin",
        "special_price",
        "override_price",
    )
    def _compute_based_on(self):
        """Determine the basis for pricing based on various fields."""
        for rec in self:
            based_on = ""

            # Determine based on which pricing strategy is being used
            if rec.special_price > 0.0:
                based_on = "Special Price"
            elif rec.override_price > 0.0:
                based_on = "Override Price"
            elif rec.override_margin > 0.0:
                based_on = "Override Margin"
            else:
                based_on = "Suggested Margin"

            # Assign determined basis to the record
            rec.based_on = based_on

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate sequence 'pa' for each record."""
        for vals in vals_list:
            seq = self.env["ir.sequence"].next_by_code("product.price.review") or "New"
            vals["name"] = seq
        return super().create(vals_list)

    def assign_to_me(self):
        """Assign the current user to the record and update state if 'new'."""
        for rec in self:
            rec.user_id = self.env.uid
            if rec.state == "new":
                rec.state = "in_progress"

    def approve(self):
        """Set the state of the record to 'validated'."""
        for rec in self:
            rec.state = "validated"

    def reject_button(self):
        """Set the state of the record to 'reject'."""
        for rec in self:
            rec.state = "reject"

    def validate_button(self):
        """Validate the price review and update corresponding product fields."""
        for rec in self:
            if rec.product_id.disable_price_reviews:
                raise ValidationError(
                    "The Disable Price Reviews option is enabled on the product."
                    " Please either reject this price review or update the product "
                    "to allow price reviews."
                )
            elif rec.product_id:
                # Update Product Values
                rec.product_id.sudo().write(
                    {
                        "tariff_percent": rec.tariff_percent,
                        "tooling_cost": rec.tooling_cost,
                        "defrayment_cost": rec.defrayment_cost,
                        "carrier_multiplier_id": rec.carrier_multiplier_id.id,
                        "total_cost": rec.total_cost,
                        "override_margin": rec.override_margin,
                        "charm_price": rec.charm_price,
                        "override_price": rec.override_price,
                        "special_price": rec.special_price,
                        "list_price": rec.final_price,
                        "based_on": rec.based_on,
                    }
                )

                # Move price review to validated state
                rec.approve()

                # Recompute the last PO Margin since it's equation values may update.
                rec.product_id.product_tmpl_id._compute_last_purchase_margin(
                    from_review=True
                )

    # END ##########
