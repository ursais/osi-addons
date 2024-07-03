from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    list_price = fields.Float(company_dependent=True)
    based_on = fields.Char(
        string="Based On",
        company_dependent=True,
    )
    total_cost = fields.Float(
        string="Approved Total Cost",
        company_dependent=True,
        help="""Total cost of product including purchase cost, tariff,
         tooling, defrayment, and shipping. Only approved Price Reviews
         update Total Cost.""",
    )
    disable_price_reviews = fields.Boolean(
        string="Disable Price Review",
        default=False,
        help="Price Reviews are not triggered when this is checked.",
    )
    enable_margin_threshold = fields.Boolean(
        string="Enable Margin Threshold",
        default=False,
        help="""Price Reviews are not triggered while enabled if Last
         PO Margin is within the acceptable margin threshold.""",
    )
    margin_min = fields.Float(
        string="Acceptable Margin - Min",
        help="Lower boundary of margin threshold.",
    )
    margin_max = fields.Float(
        string="Acceptable Margin - Max",
        help="Upper boundary of margin threshold.",
    )
    last_purchase_margin = fields.Float(
        string="Last PO Margin",
        compute="_compute_last_purchase_margin",
        store=True,
        help="""Current margin using Last PO Cost. Calculation =
         (Sales Price - [ (Last PO Cost * (1 + Tariff Percent)) +
         Tooling Cost + Defrayment Cost + Default Shipping Cost ] ) / Price""",
    )
    suggested_margin = fields.Float(
        string="Suggested Margin",
        related="categ_id.suggested_margin",
        help="Default margin if no other pricing methods are set.",
    )
    override_margin = fields.Float(
        string="Override Margin",
        company_dependent=True,
    )
    charm_price = fields.Selection(
        selection=[
            ("none", "None (No rounding)"),
            (".00", "Round to nearest dollar"),
            (".95", "Round to nearest .95 cents"),
            (".99", "Round to nearest .99 cents"),
        ],
        default="none",
        company_dependent=True,
        help="Modifies the final price based on charm price:"
        "None: No change is made to the final price."
        ".00: Rounds the price to the nearest dollar."
        ".95: Rounds the price to the nearest .95 cents."
        ".99: Rounds the price to the nearest .99 cents.",
    )
    override_price = fields.Float(
        string="Override Price",
        company_dependent=True,
    )
    special_price = fields.Float(
        string="Special Price",
        company_dependent=True,
    )
    price_currency_id = fields.Many2one(
        "res.currency",
        "Sale Price Currency",
        compute="_compute_price_currency_id",
    )
    last_purchase_price_converted = fields.Float(
        string="Last PO Cost (Currency Converted)",
        store=True,
        compute="_compute_last_purchase_price_converted",
        help="Product cost on most recent confirmed purchase",
    )

    @api.depends("company_id")
    @api.depends_context("company")
    def _compute_price_currency_id(self):
        env_currency_id = self.env.company.currency_id.id
        for template in self:
            template.price_currency_id = (
                template.company_id.currency_id.id or env_currency_id
            )

    @api.depends("last_purchase_line_id")
    def _compute_last_purchase_price_converted(self):
        for rec in self:
            if (
                rec.last_purchase_currency_id
                and rec.price_currency_id
                and rec.last_purchase_currency_id != rec.price_currency_id
            ):
                rec.last_purchase_price_converted = (
                    rec.last_purchase_currency_id._convert(
                        rec.last_purchase_price, rec.price_currency_id
                    )
                )
            else:
                rec.last_purchase_price_converted = rec.last_purchase_price

    @api.depends(
        "last_purchase_line_id",
        "carrier_multiplier_id.multiplier",
    )
    def _compute_last_purchase_margin(self, from_review=False):
        """This will compute the last purchase margin."""
        for rec in self:
            last_purchase_margin = 0
            if (
                rec.last_purchase_currency_id
                and rec.last_purchase_currency_id != rec.currency_id
            ):
                rec.last_purchase_price_converted = (
                    rec.last_purchase_currency_id._convert(
                        rec.last_purchase_price, rec.currency_id
                    )
                )
            else:
                rec.last_purchase_price_converted = rec.last_purchase_price
            if rec.list_price:
                last_purchase_margin = (
                    rec.list_price
                    - (rec.last_purchase_price_converted * (1 + rec.tariff_percent))
                    + rec.tooling_cost
                    + rec.defrayment_cost
                    + rec.default_shipping_cost
                ) / rec.list_price
            rec.last_purchase_margin = last_purchase_margin

            # If margin compute didn't come from a validated review,
            # then check if a review is needed.
            if not from_review and not rec.disable_price_reviews:
                # Don't create if last_purchase_margin is within the threshold,
                if (
                    rec.enable_margin_threshold
                    and rec.margin_max < rec.last_purchase_margin > rec.margin_min
                ):
                    return True

                # Check for open review or create one.
                else:
                    open_review = self.env["product.price.review"].search(
                        [
                            ("company_id", "=", self.env.company.id),
                            ("product_id", "=", rec.product_variant_id.id),
                            ("state", "not in", ("reject", "validated")),
                        ],
                        limit=1,
                    )
                    # If a review exists, update it by calling onchange
                    if open_review:
                        open_review.onchange_product_id()
                    # otherwise create a new review
                    else:
                        new_review = self.env["product.price.review"].create(
                            {
                                "product_id": rec.product_variant_id.id,
                                "company_id": self.env.company.id,
                            }
                        )
                        new_review.onchange_product_id()
