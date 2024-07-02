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
    _rec_name = "pa"

    # COLUMNS ##########

    # General fields on Price Review
    pa = fields.Char(
        string="Price Adjustment", requierd=True, readonly=True, default="New..."
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="[('has_configurable_attributes','=',False)]",
    )
    default_code = fields.Char(related="product_id.default_code")
    detailed_type = fields.Selection(related="product_id.detailed_type")
    categ_id = fields.Many2one(
        "product.category", string="Product Category", related="product_id.categ_id"
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
        related="product_id.product_tmpl_id.currency_id",
    )

    # Origin fields, recorded on the price review for historical purposes
    origin_last_purchase_price = fields.Float(
        string="Original Last PO Cost",
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
        help="Total cost of product including purchase cost, tariff, tooling, defrayment, and shipping.",
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
        help="Special fixed price that overrides all other pricing selections. Original price shows with strikethrough text on e-commerce platform",
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
        help="Total cost of product including purchase cost, tariff, tooling, defrayment, and shipping.",
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
        help="Special fixed price that overrides all other pricing selections. Original price shows with strikethrough text on e-commerce platform",
    )
    calculated_price = fields.Float(
        string="Calculated Price",
        compute="_compute_calculated_price",
        help="Price calculation based on Suggested and Override Margin fields set.",
    )

    # END ##########
    # METHODS ##########

    @api.onchange("product_id")
    def onchange_product_id(self):
        """Pull in all fields from product to set on the review record, for historical documentation."""
        for rec in self:
            if rec.product_id:
                # Populate historical fields on price review
                rec.origin_final_price = rec.product_id.with_company(
                    rec.company_id
                ).list_price
                rec.origin_purchase_line_id = rec.product_id.with_company(
                    rec.company_id
                ).last_purchase_line_id.id
                rec.origin_vendor_id = rec.product_id.with_company(
                    rec.company_id
                ).last_purchase_line_id.order_id.partner_id.id
                rec.origin_purchase_id = rec.product_id.with_company(
                    rec.company_id
                ).last_purchase_line_id.order_id.id
                rec.origin_last_purchase_price = rec.product_id.with_company(
                    rec.company_id
                ).last_purchase_line_id.price_unit
                rec.origin_tariff_percent = rec.product_id.with_company(
                    rec.company_id
                ).tariff_percent
                rec.origin_tooling_cost = rec.product_id.with_company(
                    rec.company_id
                ).tooling_cost
                rec.origin_defrayment_cost = rec.product_id.with_company(
                    rec.company_id
                ).defrayment_cost
                rec.origin_carrier_multiplier_id = rec.product_id.with_company(
                    rec.company_id
                ).carrier_multiplier_id
                rec.origin_default_shipping_cost = rec.product_id.with_company(
                    rec.company_id
                ).default_shipping_cost
                rec.origin_total_cost = rec.product_id.with_company(
                    rec.company_id
                ).total_cost
                rec.origin_suggested_margin = rec.product_id.with_company(
                    rec.company_id
                ).suggested_margin
                rec.origin_override_margin = rec.product_id.with_company(
                    rec.company_id
                ).override_margin
                rec.origin_override_price = rec.product_id.with_company(
                    rec.company_id
                ).override_price
                rec.origin_special_price = rec.product_id.with_company(
                    rec.company_id
                ).special_price
                rec.origin_based_on = rec.product_id.with_company(
                    rec.company_id
                ).based_on
                if rec.product_id.with_company(rec.company_id).charm_price:
                    rec.origin_charm_price = rec.product_id.with_company(
                        rec.company_id
                    ).charm_price
                else:
                    rec.origin_charm_price = "none"

                # Populate proposed pricing fields so user doesn't have to reset them.
                rec.tariff_percent = rec.product_id.with_company(
                    rec.company_id
                ).tariff_percent
                rec.tooling_cost = rec.product_id.with_company(
                    rec.company_id
                ).tooling_cost
                rec.defrayment_cost = rec.product_id.with_company(
                    rec.company_id
                ).defrayment_cost
                rec.carrier_multiplier_id = rec.product_id.with_company(
                    rec.company_id
                ).carrier_multiplier_id
                rec.override_margin = rec.product_id.with_company(
                    rec.company_id
                ).override_margin
                rec.charm_price = rec.product_id.with_company(
                    rec.company_id
                ).charm_price
                rec.override_price = rec.product_id.with_company(
                    rec.company_id
                ).override_price
                rec.special_price = rec.product_id.with_company(
                    rec.company_id
                ).special_price
                rec.based_on = rec.product_id.with_company(rec.company_id).based_on

    # ONCHANGE METHODS
    @api.onchange("user_id")
    def onchange_user_id(self):
        for rec in self:
            if rec.user_id and rec.state == "new":
                rec.state = "in_progress"

    @api.depends("carrier_multiplier_id", "product_id.weight")
    def _compute_default_shipping_cost(self):
        default_shipping_cost = 0.0
        for rec in self:
            if rec.carrier_multiplier_id:
                default_shipping_cost = (
                    rec.product_id.weight * rec.carrier_multiplier_id.multiplier
                )
            rec.default_shipping_cost = default_shipping_cost

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq = self.env["ir.sequence"].next_by_code("product.price.review") or "New"
            vals["pa"] = seq
        return super().create(vals_list)

    # COMPUTE METHODS
    @api.depends(
        "origin_final_price",
        "origin_last_purchase_price",
        "origin_tariff_percent",
        "origin_tooling_cost",
        "origin_defrayment_cost",
        "origin_default_shipping_cost",
    )
    def _compute_last_purchase_margin(self):
        for rec in self:
            last_purchase_margin = 0
            if rec.product_id.list_price:
                last_purchase_margin = (
                    rec.product_id.list_price
                    - (rec.origin_last_purchase_price * (1 + rec.origin_tariff_percent))
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
        for rec in self:
            rec.total_cost = (
                rec.origin_last_purchase_price * (1 + rec.tariff_percent)
                + rec.tooling_cost
                + rec.defrayment_cost
                + rec.default_shipping_cost
            )

    @api.depends(
        "total_cost",
        "origin_total_cost",
    )
    def _compute_cost_delta(self):
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
        for rec in self:
            final_price = 0
            # Use override price if exists, otherwise set final price based on computed
            if rec.override_price:
                final_price = rec.override_price
            else:
                final_price = rec.calculated_price

                # Apply Charm Pricing
                if rec.charm_price == ".00":
                    final_price = round(final_price)  # Round to nearest .00
                elif rec.charm_price == ".95":
                    final_price = round(final_price) - 0.05  # Round to nearest .95
                elif rec.charm_price == ".99":
                    final_price = round(final_price) - 0.01  # Round to nearest .99
                else:
                    final_price = final_price
            rec.final_price = final_price

    @api.depends("final_price", "total_cost")
    def _compute_margins(self):
        for rec in self:
            margin = 0
            margin_percent = 0
            if rec.final_price:
                margin = rec.final_price - rec.total_cost
                margin_percent = margin / rec.final_price
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
        for rec in self:
            based_on = ""
            # if rec.special_price > 0.0:
            #     based_on = "Special Price"
            if rec.override_price > 0.0:
                based_on = "Override Price"
            elif rec.override_margin > 0.0:
                based_on = "Override Margin"
            else:
                based_on = "Suggested Margin"
            rec.based_on = based_on

    def assign_to_me(self):
        for rec in self:
            rec.user_id = self.env.uid
            if rec.state == "new":
                rec.state = "in_progress"

    def approve(self):
        for rec in self:
            rec.state = "validated"

    def reject_button(self):
        for rec in self:
            rec.state = "reject"

    def validate_button(self):
        for rec in self:
            if rec.product_id and not rec.product_id.disable_price_reviews:
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
                # Recompute the last PO Margin since it's equation values may update.
                rec.product_id.product_tmpl_id._compute_last_purchase_margin(
                    from_review=True
                )
                # Move price review to approved/validated state
                rec.approve()

    # END ##########