# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # COLUMNS ##########

    list_price = fields.Float(company_dependent=True, default=0.0)
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

    # END ##########
    # METHODS ##########

    @api.depends("company_id")
    @api.depends_context("company")
    def _compute_price_currency_id(self):
        """
        Compute the price currency ID for each record based on the company's currency.

        This method calculates the currency ID (`price_currency_id`) for each record (`template`)
        in the current environment (`self`) based on the company's currency (`company_id.currency_id`)
        or falls back to the default currency of the environment if the company's currency is not set.

        Dependencies:
        - company_id: Trigger the computation whenever `company_id` changes.
        - company: Takes the current company context into account.

        Returns:
        - None
        """
        env_currency_id = self.env.company.currency_id.id
        for template in self:
            template.price_currency_id = (
                template.company_id.currency_id.id or env_currency_id
            )

    @api.depends("last_purchase_line_id")
    def _compute_last_purchase_price_converted(self):
        """
        Compute the converted last purchase price for each record.

        This method computes the converted last purchase price (`last_purchase_price_converted`)
        for each record (`rec`) in the current environment (`self`). It checks if the currency
        of the last purchase (`last_purchase_currency_id`) and the price currency (`price_currency_id`)
        differ. If they do, it converts the last purchase price (`last_purchase_price`) to
        the price currency using `_convert` method of `last_purchase_currency_id`.

        Dependencies:
        - last_purchase_line_id: Trigger the computation whenever `last_purchase_line_id` changes.

        Returns:
        - None
        """
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
    )
    def _compute_last_purchase_margin(self, from_review=False, from_threshold=False):
        """This will compute the last purchase margin."""
        for rec in self:
            # if rec.last_purchase_line_id.state in ("purchase", "done"):
            last_purchase_margin = rec.last_purchase_margin or 0.0

            # Convert last purchase price if different currency
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

            # Calculate last purchase margin based on various costs
            if rec.list_price:
                last_purchase_margin = (
                    rec.list_price
                    - (rec.last_purchase_price_converted * (1 + rec.tariff_percent))
                    + rec.tooling_cost
                    + rec.defrayment_cost
                    + (rec.default_shipping_cost or 0.0)
                ) / rec.list_price

            margin_changed = False
            if last_purchase_margin != rec.last_purchase_margin:
                rec.last_purchase_margin = last_purchase_margin
                margin_changed = True

            # If margin compute didn't come from a validated review,
            # then check if a review is needed.
            if (
                (margin_changed or from_threshold)
                and not from_review
                and not rec.disable_price_reviews
            ):
                # Check if last_purchase_margin is within threshold
                if rec.enable_margin_threshold:
                    if (
                        last_purchase_margin < rec.margin_min
                        or last_purchase_margin > rec.margin_max
                    ):
                        # If outside of threshold then create/update review
                        self._create_or_update_price_review(rec)

                # Otherwise if enabled threshold not set then create/update review
                elif not rec.enable_margin_threshold:
                    self._create_or_update_price_review(rec)

    @api.model
    def _create_or_update_price_review(self, rec):
        """Helper method to update or create a new price review."""
        # Search for an existing open review
        open_review = self.env["product.price.review"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("product_id", "=", rec.product_variant_id.id),
                ("state", "not in", ("reject", "validated")),
            ],
            limit=1,
        )

        # Update existing review if found
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

    def write(self, vals):
        """When the Min or Max threshold values change, this might need to trigger
        a price review. This will trigger the _compute_last_purchase_margin to
        check and update/create one if needed."""
        res = super().write(vals)
        for rec in self:
            if "margin_min" in vals or "margin_max" in vals:
                rec._compute_last_purchase_margin(from_threshold=True)
        return res
