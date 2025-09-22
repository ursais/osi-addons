# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleEstimateJob(models.Model):
    """Add button to create new ECO/Product/BoM for Prototypes."""

    _inherit = "sale.estimate.job"

    # COLUMNS ######

    product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="estimate_id",
        string="Product Templates",
    )
    product_count = fields.Integer(
        string="Prototype Count",
        compute="_compute_product_count",
    )
    mrp_eco_ids = fields.One2many(
        comodel_name="mrp.eco",
        inverse_name="estimate_id",
        string="ECOs",
    )
    mrp_eco_count = fields.Integer(
        string="ECO Count",
        compute="_compute_mrp_eco_count",
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost_margin",
        store=True,
    )
    margin = fields.Float(
        string="Margin",
        compute="_compute_total_cost_margin",
        store=True,
    )
    margin_percent = fields.Float(
        string="Margin (%)",
        compute="_compute_total_cost_margin",
        store=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        required=True,
        compute="_compute_warehouse_id",
        store=True,
        readonly=False,
        precompute=True,
        check_company=True,
    )
    has_active_pricelist = fields.Boolean(
        string="Has Pricelist",
        compute="_compute_has_active_pricelist",
    )
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed",
        store=False,
    )
    show_update_purchase_price = fields.Boolean(
        string="Ha Purchase Price Changed",
        compute="_compute_show_update_purchase_price",
    )
    quotation_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="estimate_id",
        string="Sales Quotations",
        readonly=True,
        copy=False,
    )
    quotation_count = fields.Integer(
        string="Quotation Count",
        compute="_compute_quotation_count",
    )

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        string="Company",
    )

    customer_request_date = fields.Date(string="Customer Request Date")

    # END ##########
    # METHODS ##########

    @api.depends("quotation_ids")
    def _compute_quotation_count(self):
        """Standard count method to count related Quotation's for smart button."""
        for lead in self:
            lead.quotation_count = len(lead.quotation_ids)

    def _compute_show_update_purchase_price(self):
        for rec in self:
            rec.show_update_purchase_price = False
            if rec.estimate_ids:
                rec.show_update_purchase_price = bool(
                    rec.estimate_ids.filtered(
                        lambda l: l.product_id.approved_total_cost != l.purchase_price
                    )
                )

    def action_update_purchase_price(self):
        for rec in self:
            for line in rec.estimate_ids.filtered(
                lambda l: l.product_id.approved_total_cost != l.purchase_price
            ):
                line.purchase_price = line.product_id.approved_total_cost

    def action_update_prices(self):
        self.ensure_one()

        self._recompute_prices()

        if self.pricelist_id:
            message = _(
                "Product prices have been recomputed according to pricelist %s.",
                self.pricelist_id._get_html_link(),
            )
        else:
            message = _("Product prices have been recomputed.")
        self.message_post(body=message)

    def _get_update_prices_lines(self):
        """Hook to exclude specific lines which should not be updated
        based on price list recomputation"""
        return self.estimate_ids.filtered(lambda line: line.job_type == "material")

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_show_update_prices(self):
        self.show_update_pricelist = bool(self.estimate_ids)

    def _recompute_prices(self):
        lines_to_recompute = self._get_update_prices_lines()
        for line in lines_to_recompute:
            line.product_id_change()
        self.show_update_pricelist = False

    @api.depends("company_id")
    def _compute_has_active_pricelist(self):
        for order in self:
            order.has_active_pricelist = bool(
                self.env["product.pricelist"].search(
                    [
                        ("company_id", "in", (False, order.company_id.id)),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
            )

    @api.depends("user_id", "company_id")
    def _compute_warehouse_id(self):
        for rec in self:
            default_warehouse_id = (
                self.env["ir.default"]
                .with_company(rec.company_id.id)
                ._get_model_defaults("sale.order")
                .get("warehouse_id")
            )
            if rec.state in ["draft", "sent"] or not rec.ids:
                # Should expect empty
                if default_warehouse_id is not None:
                    rec.warehouse_id = default_warehouse_id
                else:
                    rec.warehouse_id = rec.user_id.with_company(
                        rec.company_id.id
                    )._get_default_warehouse_id()

    def open_product_creation_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.creation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_estimate_id": self.id,
                "default_opportunity_id": self.opportunity_id.id,
            },
        }

    @api.depends("product_tmpl_ids")
    def _compute_product_count(self):
        """Standard count method to count related Products's for smart button."""
        for lead in self:
            lead.product_count = len(lead.product_tmpl_ids)

    @api.depends(
        "estimate_ids",
        "estimate_ids.purchase_price",
        "labour_estimate_line_ids",
        "labour_estimate_line_ids.purchase_price",
        "overhead_estimate_line_ids",
        "overhead_estimate_line_ids.purchase_price",
    )
    def _compute_total_cost_margin(self):
        for estimate in self:
            estimate_total_cost = 0.0
            estimate_total_cost += sum(
                line.purchase_price for line in estimate.estimate_ids
            )
            estimate_total_cost += sum(
                line.purchase_price for line in estimate.labour_estimate_line_ids
            )
            estimate_total_cost += sum(
                line.purchase_price for line in estimate.overhead_estimate_line_ids
            )

            estimate.total_cost = estimate_total_cost
            estimate.margin = estimate.estimate_total - estimate_total_cost
            if estimate.estimate_total != 0.0:
                estimate.margin_percent = estimate.margin / estimate.estimate_total
            else:
                estimate.margin_percent = 0.0

    def action_view_product(self):
        """Smart button action to open the Product or list of Products if
        more than one."""
        products = self.product_tmpl_ids
        action = self.env.ref("product.product_template_action").read()[0]
        if len(products) == 1:
            # Open the single product in form view
            action["views"] = [
                (self.env.ref("product.product_template_only_form_view").id, "form"),
            ]
            action["res_id"] = products.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("product.product_template_tree_view").id, "tree"),
                (self.env.ref("product.product_template_only_form_view").id, "form"),
            ]
            action["context"] = dict(self.env.context)  # Preserve context if needed
            action["domain"] = [("id", "in", products.ids)]

        return action

    @api.depends("mrp_eco_ids")
    def _compute_mrp_eco_count(self):
        """Standard count method to count related ECO's for smart button."""
        for lead in self:
            lead.mrp_eco_count = len(lead.mrp_eco_ids)

    def action_view_eco(self):
        """Smart button action to open the ECO or list of ECO's if more than one."""
        ecos = self.mrp_eco_ids
        action = self.env.ref("mrp_plm.mrp_eco_action").read()[0]

        if len(ecos) == 1:
            # Open the single ECO in form view
            action["views"] = [
                (self.env.ref("mrp_plm.mrp_eco_view_form").id, "form"),
            ]
            action["res_id"] = ecos.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("mrp_plm.mrp_eco_view_tree").id, "tree"),
                (self.env.ref("mrp_plm.mrp_eco_view_form").id, "form"),
            ]
            action["domain"] = [("id", "in", ecos.ids)]
            action["context"] = dict(self.env.context)  # Preserve context if needed

        return action

    def create_quotation_wizard(self):
        """
        Opens a wizard for creating a quotation from selected estimate products.
        """
        if self.product_tmpl_ids:
            return {
                "type": "ir.actions.act_window",
                "name": "Create Quotation",
                "res_model": "quotation.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_estimate_id": self.id},
            }
        else:
            return self.estimate_to_quotation()

    def open_add_components(self):
        # Prepare the action to open the "Add Components" wizard
        return {
            "name": _("Add Components"),
            "type": "ir.actions.act_window",
            "res_model": "add.components.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def estimate_to_quotation(self):
        super().estimate_to_quotation()

        for rec in self:
            # Additional logic to create multiple quotations
            if (
                not rec.estimate_ids
                and not rec.labour_estimate_line_ids
                and not rec.overhead_estimate_line_ids
            ):
                raise UserError(_("Please enter Estimation Lines!"))

            # Prepare data for multiple quotations
            vals = [
                {
                    "partner_id": rec.partner_id.id,
                    "origin": rec.number + " - Additional",
                    "analytic_account_id": rec.analytic_id.id,
                    "payment_term_id": rec.payment_term_id.id,
                    "pricelist_id": rec.pricelist_id.id,
                    "opportunity_id": rec.opportunity_id.id,
                    "estimate_id": rec.id,
                }
            ]

            # Create quotation
            quotation = self.env["sale.order"].create(vals)
            rec._prepare_quotation_line(quotation)
        return {
            "type": "ir.actions.act_window",
            "name": _("Quotations"),
            "view_mode": "form",
            "res_model": "sale.order",
            "res_id": quotation.id,
            "context": self.env.context,
        }

    def view_custom_quotation(self):
        """Override since we can now have multiple quotes from estimate."""
        """Smart button action to open the Sale Order or list of Sale Order's if more than one."""
        super().view_custom_quotation()
        estimates = self.quotation_ids
        action = self.env.ref("sale.action_quotations_with_onboarding").read()[0]
        if len(estimates) == 1:
            action["views"] = [
                (
                    self.env.ref("sale.view_order_form").id,
                    "form",
                )
            ]
            action["res_id"] = estimates.id
        else:
            action["domain"] = [("id", "in", estimates.ids)]
        return action
