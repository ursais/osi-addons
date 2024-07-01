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
