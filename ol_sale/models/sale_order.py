# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order
    """

    _inherit = "sale.order"

    # COLUMNS #####
    original_request_date = fields.Date(
        string="Original Customer Requested Date",
        copy=False,
    )

    first_estimate_date = fields.Date(
        string="First Estimated Date",
        compute="_compute_first_estimate_date",
        store=True,
        copy=False,
    )

    current_estimate_ship_date = fields.Date(
        string="Current Estimated Ship Date",
        compute="_compute_current_estimate_ship_date",
        store=True,
        copy=False,
    )

    original_commitment_date = fields.Datetime(
        string="Original Customer Requested Date",
        copy=False,
    )
    account_manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Account Manager",
    )
    end_user = fields.Many2one(comodel_name="res.partner")
    integrator = fields.Many2one(comodel_name="res.partner")
    delivery_note = fields.Text(string="Delivery Note")
    mrp_note = fields.Text(string="Manufacturing Note")
    to_send_confirmation_email = fields.Boolean(
        string="Send confirmation email",
        default=True,
        copy=False,
    )

    # This field is populated via Integrations, but also used in emails
    is_guest_checkout = fields.Boolean(
        string="Guest checkout",
        copy=False,
    )
    contact_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Contact(s)",
        compute="_compute_contact_ids",
        store=True,
        readonly=False,
        help="These are the contacts that will receive automated email communications.",
    )
    shipping_ref = fields.Char(string="Shipping Reference")
    has_active_holds = fields.Boolean(compute="_compute_has_active_holds")
    invoice_status = fields.Selection(
        selection_add=[
            ("partially invoiced", "Partially Invoiced"),
            ("full paid", "Fully Paid"),
        ]
    )
    mo_tranfer_count = fields.Integer(
        string="MO Intenral Tranfer",
        compute="_compute_mo_tranfer_count",
    )
    request_date_change_pending = fields.Boolean(
        string="Customer Request Date Change Proposed",
        default=False,
        copy=False,
    )

    # END #########

    # METHODS #########

    def _check_component_out_of_stock(self):
        """Method used in the component out of stock exception"""
        for order in self:
            for line in order.order_line:
                if (
                    not line.product_id.allow_backorder
                    and line.product_id.type == "product"
                    and not line.bom_id
                ):
                    if (
                        line.product_id.qty_available < line.product_uom_qty
                        and line.product_id.incoming_qty < line.product_uom_qty
                    ):
                        return True
                if line.bom_id:
                    for component in line.bom_id.bom_line_ids:
                        product = component.product_id
                        required_qty = line.product_uom_qty * component.product_qty
                        if not product.allow_backorder and product.type == "product":
                            if (
                                product.qty_available < component.product_qty
                                and product.incoming_qty < required_qty
                            ):
                                return True
        return False

    def _compute_has_active_holds(self):
        def has_hold_in_bom(product, company):
            """Recursively check for sale_ok on all components and subcomponents."""
            bom_by_product = self.env["mrp.bom"]._bom_find(
                products=product, company_id=company.id
            )
            bom = bom_by_product.get(product)
            if not bom:
                return False

            for bom_line in bom.bom_line_ids:
                component = bom_line.product_id
                if not component.sale_ok:
                    return True
                if has_hold_in_bom(component, company):
                    return True
            return False

        for sale in self:
            has_hold = False
            for line in sale.order_line:
                if not line.product_id.sale_ok:
                    has_hold = True
                    break
                if line.bom_id:
                    for bom_line in line.bom_id.bom_line_ids:
                        component = bom_line.product_id
                        if not component.sale_ok or has_hold_in_bom(
                            component, sale.company_id
                        ):
                            has_hold = True
                            break
                    if has_hold:
                        break
            sale.has_active_holds = has_hold

    @api.depends("partner_id")
    def _compute_contact_ids(self):
        """Auto set the contact_ids field with Partner, then user can change if desired."""
        for order in self:
            if order.partner_id:
                order.contact_ids = [(6, 0, [order.partner_id.id])]
            else:
                order.contact_ids = [(5, 0, 0)]

    def action_confirm(self):
        """
        Inherit method for set up value for original_request_date and original_commitment_date
        """

        # First check for original request date and raise validation error if not set
        for rec in self:
            if not rec.commitment_date:
                raise ValidationError(
                    _(
                        "Customer Request Date is required for orders before confirmation."
                    )
                )

            # store original commitment date on first confirmation (do not overwrite)
            if not rec.original_commitment_date and rec.commitment_date:
                rec.original_commitment_date = fields.Date.to_date(rec.commitment_date)

        # Call the parent method once for all records
        res = super().action_confirm()

        # Send confirmation email
        self.send_confirmation_email()

        # Disable the flag post-confirmation to prevent duplicate emails
        if not self.detect_exceptions():
            self.to_send_confirmation_email = False

        # # Update original_commitment_date for each record after confirmation
        # for rec in self:
        #     rec.original_commitment_date = self.commitment_date or self.expected_date
        return res

    @api.onchange("partner_id")
    def _onchange_partner_id_sale_order_tag_ids(self):
        self.tag_ids = self.partner_id.sale_order_tag_ids

    @api.onchange("partner_id")
    def _onchange_partner_id_account_manager(self):
        self.account_manager_id = self.partner_id.account_manager_id

    def get_quote_report_data(self):
        """Get the Sale Order related report data"""

        data = {}
        for order in self:
            order_data = order.get_report_data()
            data[order.id] = order_data
        return data

    def get_report_data(self):
        """Collect order information into a dict, that can be used in reports"""

        self.ensure_one()

        order_data = {
            "product_lines": [],
        }

        product_lines = self.with_context(
            lang=self.contact_ids and self.contact_ids[0].lang or self.partner_id.lang
        ).order_line.filtered(lambda l: not l.is_delivery)

        for sale_order_line in product_lines:
            quote_config = sale_order_line.config_session_id or False
            product = sale_order_line.product_id
            bom_line_ids = sale_order_line.bom_id.mapped("bom_line_ids")
            template_attr_values = []

            if product and product.product_template_attribute_value_ids:
                visible_values = product.product_template_attribute_value_ids.filtered(
                    lambda v: v.visible_to_user
                ).sorted(key=lambda v: v.attribute_id.sequence)

                # Prepare the configuration lines to match the structure you had before
                template_attr_values = [
                    {
                        "attribute_id": v.attribute_id,
                        "attribute_name": v.attribute_id.name,
                        "value_name": v.product_attribute_value_id.product_id.name
                        or v.product_attribute_value_id.name,
                        "sequence": v.attribute_id.sequence,
                        "product_qty": int(
                            sum(
                                bom_line_ids.filtered(
                                    lambda bom_line: bom_line.product_id.id
                                    == v.product_id.id
                                ).mapped("product_qty")
                            )
                        )
                        or 1,
                    }
                    for v in visible_values
                ]
            order_line_data = {
                "order_line": sale_order_line,
                "quote_config": quote_config,
                "quote_lines": template_attr_values,
            }

            order_data["product_lines"].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.order_line.filtered(lambda l: l.is_delivery)

        order_data["shipping_lines"] = shipping_lines
        order_data["product_subtotal_amount"] = sum(
            product_lines.mapped("price_subtotal")
        )
        order_data["shipping_subtotal_amount"] = sum(
            shipping_lines.mapped("price_subtotal")
        )
        return order_data

    def _send_order_confirmation_mail(self):
        """
        We don't want core to send anything, we handle the order confirmation email ourselves
        """
        return

    def toggle_confirmation_email(self):
        """
        Toggle whether to send the email or not
        """
        for order in self:
            order.to_send_confirmation_email = not order.to_send_confirmation_email

    def send_confirmation_email(self):
        """
        Send a Sale Order confirmation email
        """
        self.ensure_one()

        if not self.to_send_confirmation_email:
            return
        if self.detect_exceptions():
            return

        # Create and send the email based on the confirmation template immediately
        self.env.ref(
            "ol_sale.order_confirmation_email_template"
        ).send_email_with_terms_and_conditions(self.company_id, self.id)

    def action_open_forward_confirmation_email_wizard(self):
        """Open forward confirmation wizard"""
        self.ensure_one()

        return self.env.ref("ol_sale.action_forward_confirmation_email_wizard").read()[
            0
        ]

    def _get_new_rev_data(self, new_rev_number=None):
        self.ensure_one()
        # Find the max revision number for this unrevisioned_name + company
        domain = [
            ("unrevisioned_name", "=", self.unrevisioned_name),
            ("company_id", "=", self.company_id.id),
        ]
        all_revisions = self.search(domain, order="revision_number desc", limit=1)
        new_rev_number = (all_revisions.revision_number or 0) + 1
        return {
            "revision_number": new_rev_number,
            "unrevisioned_name": self.unrevisioned_name,
            "name": "%s-%02d" % (self.unrevisioned_name, new_rev_number),
            "old_revision_ids": [(4, self.id, False)],
        }

    def _find_mail_template(self):
        self.ensure_one()

        template = None

        # Proforma Email
        if self.env.context.get("proforma"):
            template = self.env.ref(
                "ol_sale.email_template_sale_proforma", raise_if_not_found=False
            )

        # Budgetary Quote Email
        elif self.type_id.name == "Budgetary":
            template = self.env.ref(
                "ol_sale.budgetary_quote_template", raise_if_not_found=False
            )

        # Click to Buy Email (default for others)
        else:
            template = self.env.ref(
                "ol_sale.order_click_to_buy_email_template", raise_if_not_found=False
            )

        # Use found template, otherwise fallback
        return template or super()._find_mail_template()

    @api.depends("mrp_production_ids.picking_ids.batch_id")
    def _compute_mo_tranfer_count(self):
        for rec in self:
            pickings = rec.mrp_production_ids.mapped("picking_ids")
            batch_pickings = pickings.mapped("batch_id")
            if batch_pickings:
                rec.mo_tranfer_count = len(batch_pickings)
            else:
                rec.mo_tranfer_count = len(pickings)

    def action_view_mo_internal_picking(self):
        self.ensure_one()
        pickings = self.mrp_production_ids.mapped("picking_ids")
        batch_pickings = pickings.mapped("batch_id")

        action = None
        if batch_pickings:
            # Open batch pickings
            action = self.env["ir.actions.actions"]._for_xml_id(
                "stock_picking_batch.stock_picking_batch_action"
            )
            if len(batch_pickings) > 1:
                action["domain"] = [("id", "in", batch_pickings.ids)]
            else:
                action["res_id"] = batch_pickings.id
                action["views"] = [
                    (
                        self.env.ref("stock_picking_batch.stock_picking_batch_form").id,
                        "form",
                    )
                ]
        else:
            # Fall back to normal pickings
            action = self.env["ir.actions.actions"]._for_xml_id(
                "stock.action_picking_tree_all"
            )
            if len(pickings) > 1:
                action["domain"] = [("id", "in", pickings.ids)]
            elif pickings:
                action["res_id"] = pickings.id
                action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
                if "views" in action:
                    action["views"] += [
                        (state, view)
                        for state, view in action["views"]
                        if view != "form"
                    ]

        action["context"] = dict(self._context)
        return action

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if "partner_shipping_id" in vals:
            for order in self.filtered(lambda a: a.state == "sale"):
                for picking in order.picking_ids.filtered(
                    lambda p: p.state not in ["done", "cancel"]
                ):
                    picking.partner_id = order.partner_shipping_id
        return res

    @api.onchange(
        "order_line",
        "tax_on_shipping_address",
        "tax_address_id",
        "partner_id",
    )
    def onchange_avatax_calculation(self):
        """
        Super avatax calculate taxes method, so instead of raising error if no lines
        are on the sale order and the 'compute tax on so save' option is enabled, then
        we just don't compute taxes. Raising an error causes a problem when clicking
        the product configurator button because it saves the SO before opening the
        wizard.
        """
        avatax_config = self.env.company.get_avatax_config_company()
        if avatax_config and avatax_config.sale_calculate_tax and not self.order_line:
            return
        super().onchange_avatax_calculation()

    @api.depends("state", "order_line.invoice_status", "order_line.is_downpayment")
    def _compute_invoice_status(self):
        for order in self:
            # Default for non-eligible states
            if order.state not in ("sale", "sent"):
                order.invoice_status = "no"
                continue

            # Check if we’re in the special Bank Transfer + sent case
            if (
                order.state == "sent"
                and order.sale_payment_method_id.name != "Bank Transfer"
            ):
                order.invoice_status = "no"
                continue

            # --- New downpayment-based coverage logic ---
            downpayment_lines = order.order_line.filtered("is_downpayment")
            dp_invoice_lines = downpayment_lines.mapped("invoice_lines")
            dp_total = sum(dp_invoice_lines.mapped("price_subtotal"))
            order_total = order.amount_untaxed

            if dp_total >= order_total:
                # fully covered by downpayment
                if all(
                    move.payment_state in ("in_payment", "paid")
                    for move in dp_invoice_lines.mapped("move_id")
                ):
                    order.invoice_status = "full paid"
                else:
                    order.invoice_status = "invoiced"
                continue
            elif 0 < dp_total < order_total:
                order.invoice_status = "partially invoiced"
                continue

            # --- Fallback to line-driven logic (normal Odoo aggregation) ---
            line_statuses = order.order_line.filtered(
                lambda l: not l.is_downpayment
            ).mapped("invoice_status")
            if any(st == "to invoice" for st in line_statuses):
                order.invoice_status = "to invoice"
            elif line_statuses and all(st == "invoiced" for st in line_statuses):
                order.invoice_status = "invoiced"
            elif line_statuses and all(
                st in ("invoiced", "upselling") for st in line_statuses
            ):
                order.invoice_status = "upselling"
            elif any(st == "partially invoiced" for st in line_statuses):
                order.invoice_status = "partially invoiced"
            elif line_statuses and all(st == "full paid" for st in line_statuses):
                order.invoice_status = "full paid"
            else:
                order.invoice_status = "no"

    @api.depends(
        "commitment_date",
        "mrp_production_ids",
        "mrp_production_ids.mrp_batch_id",
        "mrp_production_ids.mrp_batch_id.components_availability",
        "mrp_production_ids.mrp_batch_id.components_availability_state",
    )
    def _compute_current_estimate_ship_date(self):
        for sale in self:
            sale.current_estimate_ship_date = False
            commitment_date = sale.commitment_date
            current_estimate_ship_date = commitment_date
            mrp_batch_data = self.env["mrp.production.batch"].search(
                [("sale_order_ids", "in", sale.id)]
            )
            if mrp_batch_data:
                batch_dates = mrp_batch_data.mapped("estimated_ship_date")
                batch_dates = [d for d in batch_dates if d]  # filter out False/None
                if batch_dates:
                    # take the latest of the batches and commitment_date
                    current_estimate_ship_date = max(
                        max(batch_dates),
                        commitment_date.date() if commitment_date else max(batch_dates),
                    )
            sale.current_estimate_ship_date = current_estimate_ship_date

    @api.depends("commitment_date", "expected_date")
    def _compute_first_estimate_date(self):
        for sale in self:
            if sale.commitment_date and sale.expected_date:
                sale.first_estimate_date = max(sale.commitment_date, sale.expected_date)

    @api.onchange("commitment_date", "expected_date")
    def _onchange_commitment_date(self):
        super()._onchange_commitment_date()
        mo_batchs = self.env["mrp.production.batch"].search(
            [("sale_order_ids", "in", self._origin.id)]
        )
        if mo_batchs and self.commitment_date and self.state not in ("sale", "done"):
            mo_batchs.write(
                {
                    "date_change_exception": True,
                    "customer_request_date_proposed": self.commitment_date,
                }
            )
            if mo_batchs.production_ids:
                mo_batchs.production_ids.write({"date_change_exception": True})

    # END #########
