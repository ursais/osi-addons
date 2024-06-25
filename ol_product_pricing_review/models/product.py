from odoo import fields, api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends("last_purchase_price")
    def _compute_last_purchase_margin(self):
        for rec in self:
            last_purchase_margin = 0
            if rec.list_price:
                last_purchase_margin = (
                    rec.list_price
                    - (rec.last_purchase_price * (1 + rec.tariff_percent))
                    + rec.tooling_cost
                    + rec.defrayment_cost
                    + rec.default_shipping_cost
                ) / rec.list_price
            rec.last_purchase_margin = last_purchase_margin

    based_on = fields.Char(string="Based On")
    total_cost = fields.Float(
        string="Total Cost",
        help="Total cost of product including purchase cost, tariff, tooling, defrayment, and shipping. Only approved Price Reviews update Total Cost.",
    )
    disable_price_reviews = fields.Boolean(
        string="Disable Price Review",
        default=False,
        help="Price Reviews are not triggered when this is checked.",
    )
    enable_margin_threshold = fields.Boolean(
        string="Enable Margin Threshold",
        default=False,
        help="Price Reviews are not triggered while enabled if Last PO Margin is within the acceptable margin threshold.",
    )
    margin_min = fields.Float(
        string="Acceptable Margin - Min", help="Lower boundary of margin threshold."
    )
    margin_max = fields.Float(
        string="Acceptable Margin - Max", help="Upper boundary of margin threshold."
    )
    last_purchase_margin = fields.Float(
        string="Last PO Margin",
        compute="_compute_last_purchase_margin",
        help="Current margin using Last PO Cost. Calculation = (Sales Price - [ (Last PO Cost * (1 + Tariff Percent)) + Tooling Cost + Defrayment Cost + Default Shipping Cost ] ) / Price",
    )
    suggested_margin = fields.Float(
        string="Suggested Margin",
        related="categ_id.suggested_margin",
        help="Default margin if no other pricing methods are set.",
    )
    override_margin = fields.Float(string="Override Margin")
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
    override_price = fields.Float(string="Override Price")
    special_price = fields.Float(string="Special Price")


class ProducProduct(models.Model):
    _inherit = "product.product"

    price_review_count = fields.Integer(
        "# Price Reviews",
        compute="_compute_price_review",
    )

    def _compute_price_review(self):
        """Computes the number of price reviews to show in the smart button."""
        for rec in self:
            rec.price_review_count = self.env["product.price.review"].search_count(
                [
                    ("product_id", "=", rec.id),
                ]
            )

    def action_view_price_reviews(self):
        """Action to open related price reviews from smart button."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ol_product_pricing_review.product_open_price_review"
        )
        action["context"] = {
            "default_product_id": self.id or False,
            "search_default_review_state_draft": True,
            "search_default_review_state_in_progress": True,
        }
        action["domain"] = [("product_id", "in", self.ids)]
        return action

    def action_price_review(self):
        """Action for the Price Review button, opens an existing
        review (Draft/In Progress), otherwise opens a new one."""
        open_review = self.env["product.price.review"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("product_id", "=", self.id),
                ("state", "not in", ("reject", "validated")),
            ],
            limit=1,
        )
        view = self.env.ref("ol_product_pricing_review.product_price_review_form_view")
        if open_review:
            return {
                "res_model": "product.price.review",
                "type": "ir.actions.act_window",
                "context": {},
                "view_mode": "form",
                "view_type": "form",
                "res_id": open_review.id,
                "view_id": view.id,
                "target": "current",
            }
        else:
            return {
                "res_model": "product.price.review",
                "type": "ir.actions.act_window",
                "context": {"default_product_id": self.id},
                "view_mode": "form",
                "view_type": "form",
                "view_id": view.id,
                "target": "current",
            }
