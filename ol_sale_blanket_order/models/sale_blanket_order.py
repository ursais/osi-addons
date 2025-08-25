# Import Odoo libs
import logging
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleBlanketOrder(models.Model):
    """
    Add new fields to Sale blanket Order
    """

    _inherit = "sale.blanket.order"

    # COLUMNS #####

    auto_release = fields.Boolean(
        default=True,
        tracking=True,
        help="Automates the release of blanket order lines on scheduled date minus customer lead time.",
    )
    partner_invoice_id = fields.Many2one(
        comodel_name="res.partner",
        string="Invoice Address",
        compute="_compute_partner_invoice_id",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        check_company=True,
        help="The invoice address that will be set on the sale orders when they are generated.",
    )
    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner",
        string="Delivery Address",
        compute="_compute_partner_shipping_id",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        check_company=True,
        help="The shipping address to be used on sale orders.",
    )
    contact_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Contact(s)",
        compute="_compute_contact_ids",
        store=True,
        readonly=False,
        help="These are the contacts that will receive automated email communications.",
    )
    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Delivery Method",
        check_company=True,
        help="Fill this field if you plan to invoice the shipping based on picking.",
    )
    show_update_pricelist = fields.Boolean(string="Has Pricelist Changed", store=False)
    has_active_pricelist = fields.Boolean(compute="_compute_has_active_pricelist")
    margin = fields.Monetary(
        string="Margin",
        compute="_compute_margin",
        store=True,
    )
    margin_percent = fields.Float(
        string="Margin (%)",
        compute="_compute_margin",
        store=True,
        group_operator="avg",
    )
    account_manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Account Manager",
    )

    sale_payment_method_id = fields.Many2one(
        comodel_name="payment.method",
        string="Customer Payment Method",
        help="Payment method selected coming from the sale order.",
    )

    # END #########
    # METHODS #####

    @api.depends("line_ids.margin", "amount_untaxed")
    def _compute_margin(self):
        if not all(self._ids):
            for order in self:
                order.margin = sum(order.line_ids.mapped("margin"))
                order.margin_percent = (
                    order.amount_untaxed and order.margin / order.amount_untaxed
                )
        else:
            # On batch records recomputation (e.g. at install), compute the margins
            # with a single read_group query for better performance.
            # This isn't done in an onchange environment because (part of) the data
            # may not be stored in database (new records or unsaved modifications).
            grouped_order_lines_data = self.env["sale.blanket.order.line"]._read_group(
                [
                    ("order_id", "in", self.ids),
                ],
                ["order_id"],
                ["margin:sum"],
            )
            mapped_data = {
                order.id: margin for order, margin in grouped_order_lines_data
            }
            for order in self:
                order.margin = mapped_data.get(order.id, 0.0)
                order.margin_percent = (
                    order.amount_untaxed and order.margin / order.amount_untaxed
                )

    # END #########

    # METHODS #########

    @api.depends("partner_id")
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = (
                order.partner_id.address_get(["invoice"])["invoice"]
                if order.partner_id
                else False
            )

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = (
                order.partner_id.address_get(["delivery"])["delivery"]
                if order.partner_id
                else False
            )

    @api.depends("partner_id")
    def _compute_contact_ids(self):
        """Auto set the contact_ids field with Partner, then user can change if desired."""
        for order in self:
            if order.partner_id:
                order.contact_ids = [(6, 0, [order.partner_id.id])]
            else:
                order.contact_ids = [(5, 0, 0)]  # Clears all

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

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        self.carrier_id = self.partner_id.property_delivery_carrier_id
        self.account_manager_id = self.partner_id.account_manager_id
        self.sale_payment_method_id = self.partner_id.sale_payment_method_id
        return res

    @api.onchange("company_id")
    def _onchange_company_id_warning(self):
        self.show_update_pricelist = True
        if self.line_ids and self.state == "draft":
            return {
                "warning": {
                    "title": _("Warning for the change of your quotation's company"),
                    "message": _(
                        "Changing the company of an existing quotation might need some "
                        "manual adjustments in the details of the lines. You might "
                        "consider updating the prices."
                    ),
                }
            }

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_show_update_prices(self):
        self.show_update_pricelist = bool(self.line_ids)

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

    def _recompute_prices(self):
        lines_to_recompute = self._get_update_prices_lines()
        lines_to_recompute.invalidate_recordset(["pricelist_item_id"])
        for line in lines_to_recompute:
            line.with_context(update_pricelist=True).onchange_product()
        self.show_update_pricelist = False

    def _get_update_prices_lines(self):
        """Hook to exclude specific lines which should not be updated based on price list recomputation"""
        return self.line_ids.filtered(lambda line: not line.display_type)

    def action_confirm(self):
        """Check the Scheduled Date in BOL before confirm."""
        for order in self:
            if order.line_ids.filtered(lambda l: not l.date_schedule):
                raise ValidationError(
                    _(
                        "Scheduled Date is required on blanket order lines to confirm an order"
                    )
                )
        return super().action_confirm()

    def _prepare_so_line_vals(self, line):
        """Prepares the values for a sale order line based on the
        provided blanket order line."""
        return {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.sequence,
            "price_unit": line.price_unit,
            "blanket_order_line": line.id,
            "product_uom_qty": line.remaining_uom_qty,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "customer_lead": line.customer_lead,
        }

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
        original_request_date,
        partner_invoice_id,
        partner_shipping_id,
        contact_ids,
    ):
        # Prepares the values for creating a sale order based on the provided details.
        return {
            "partner_id": customer,
            "origin": self.name,
            "user_id": user_id,
            "currency_id": currency_id,
            "pricelist_id": pricelist_id,
            "payment_term_id": payment_term_id,
            "order_line": order_lines_by_customer[customer],
            "analytic_account_id": self.analytic_account_id.id,
            "original_request_date": original_request_date or fields.Date.today(),
            "partner_invoice_id": partner_invoice_id,
            "partner_shipping_id": partner_shipping_id,
            "contact_ids": contact_ids,
            "ignore_exception": True,
            "account_manager_id": self.partner_id.account_manager_id.id,
            "sale_payment_method_id": self.sale_payment_method_id.id,
        }

    def create_sale_order_cron(self):
        # Scheduled method to create sale orders automatically based on blanket orders.
        # Get the current date
        today = fields.Date.today()
        # Search for open blanket orders with auto_release enabled
        blanket_orders = self.search(
            [
                ("state", "=", "open"),
                ("auto_release", "=", True),
            ]
        )

        for order in blanket_orders:
            # Dictionary to store order lines by customer
            order_lines_by_customer = defaultdict(list)
            # Initialize variables to track order attributes
            currency_id = (
                pricelist_id
            ) = (
                user_id
            ) = payment_term_id = partner_invoice_id = partner_shipping_id = None
            original_request_date = None
            contact_ids = None

            release_days = order.company_id.blanket_order_release_days
            for line in order.line_ids:
                # Check if the scheduled date plus customer lead time is due and
                # there is a remaining quantity to order
                if (
                    line.date_schedule
                    and (line.date_schedule - timedelta(days=release_days or 0.0))
                    <= today
                    and line.remaining_uom_qty > 0
                ):
                    # Check if product can be added to a quote, if not create activity
                    if not line.product_id.sale_ok:
                        order.activity_schedule(
                            "mail.mail_activity_data_warning",
                            note=_(
                                "Failed to create sale order. "
                                "Product %s is not allowed to be added to a sale order."
                                % line.product_id.display_name
                            ),
                            user_id=order.user_id.id or self.env.uid,
                        )
                        continue

                    # Prepare values for the sale order line
                    vals = self._prepare_so_line_vals(line)
                    # Group lines by customer
                    order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

                    # Find smallest scheduled date
                    if (
                        original_request_date is None
                        or line.date_schedule < original_request_date
                    ):
                        original_request_date = line.date_schedule

                    # Track and validate the consistency of currency, pricelist, user,
                    # and payment terms across lines
                    if currency_id is None:
                        currency_id = line.order_id.currency_id.id
                    elif currency_id != line.order_id.currency_id.id:
                        currency_id = False

                    if partner_invoice_id is None:
                        partner_invoice_id = line.order_id.partner_invoice_id.id
                    elif partner_invoice_id != line.order_id.partner_invoice_id.id:
                        partner_invoice_id = False

                    if partner_shipping_id is None:
                        partner_shipping_id = line.order_id.partner_shipping_id.id
                    elif partner_shipping_id != line.order_id.partner_shipping_id.id:
                        partner_shipping_id = False

                    if contact_ids is None:
                        contact_ids = line.order_id.contact_ids.ids

                    if pricelist_id is None:
                        pricelist_id = line.pricelist_id.id
                    elif pricelist_id != line.pricelist_id.id:
                        pricelist_id = False

                    if user_id is None:
                        user_id = line.user_id.id
                    elif user_id != line.user_id.id:
                        user_id = False

                    if payment_term_id is None:
                        payment_term_id = line.payment_term_id.id
                    elif payment_term_id != line.payment_term_id.id:
                        payment_term_id = False

            # If no order lines or inconsistent currency, skip to the next order
            if not order_lines_by_customer or not currency_id:
                continue

            # Create sale orders for each customer with valid order lines
            for customer in order_lines_by_customer:
                # Prepare values for the sale order
                order_vals = order._prepare_so_vals(
                    customer,
                    user_id,
                    currency_id,
                    pricelist_id,
                    payment_term_id,
                    order_lines_by_customer,
                    original_request_date,
                    partner_invoice_id,
                    partner_shipping_id,
                    contact_ids,
                )
                sale_order = False
                try:
                    # Create the sale order
                    sale_order = self.env["sale.order"].create(order_vals)
                    # Log the creation of the sale order
                    _logger.info(
                        _(
                            f"Created sale order: {sale_order.id}, based on blanket order: {order.id}"
                        )
                    )
                except Exception as e:
                    order.activity_schedule(
                        "mail.mail_activity_data_warning",
                        note=_(f"Failed to create sale order. Reason is '{e}'"),
                        user_id=order.user_id.id or self.env.uid,
                    )

                if sale_order:
                    try:
                        # Check to make sure all products are able to be sold
                        # raise confirmation error if not which will create an activity.
                        if any(
                            not line.product_id.sale_ok_confirm
                            or not line.product_id.ship_ok
                            for line in sale_order.order_line
                        ):
                            raise ValidationError(
                                "A Product's state is preventing order confirmation."
                            )
                        # Confirm the sale order - ignore_excption is True so
                        # exceptions won't trigger
                        sale_order.action_confirm()

                        # Remove Ignore Exceptions which will also trigger exception check
                        sale_order.write({"ignore_exception": False})

                    except Exception as e:
                        sale_order.activity_schedule(
                            "mail.mail_activity_data_warning",
                            note=_(
                                f"The sale order {sale_order.name} created from Blanket Order {order.name} couldn't be confirmed. \nReason: '{e}'"
                            ),
                            user_id=sale_order.user_id.id or self.env.uid,
                        )
            # Trigger computes for remaining amount fields so bookings trigger
            order.line_ids._compute_remaining_prices()

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create method to:
        Update the Account Manager from Partner.
        """
        records = super().create(vals_list)
        for rec in self.filtered(
            lambda p: not p.account_manager_id and p.partner_id.account_manager_id
        ):
            rec.account_manager_id = rec.partner_id.account_manager_id.id
        return records

    # END #########
