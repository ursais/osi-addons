# Import Python libs
from datetime import datetime

# Import Odoo libs
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_compare


class SaleBooking(models.Model):
    _name = "sale.booking"
    _description = "Sales Booking"
    _rec_name = "origin"
    _order = "id desc, create_date desc"

    # COLUMNS ###

    origin = fields.Char(
        string="Sale/Blanket Order",
        compute="_compute_origin",
        store=True,
    )
    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
    )
    sale_order_currency_id = fields.Many2one(
        string="Sale Order Currency",
        comodel_name="res.currency",
        related="order_id.pricelist_id.currency_id",
    )
    blanket_order_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Sale Blanket Order",
    )
    sale_blanket_order_currency_id = fields.Many2one(
        string="Sale Blanket Order Currency",
        comodel_name="res.currency",
        related="blanket_order_id.pricelist_id.currency_id",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        compute="_compute_currency_id",
        store=True,
    )
    partner_id = fields.Many2one(
        string="Customer",
        comodel_name="res.partner",
        related="order_id.partner_id",
        store=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        related="order_id.user_id",
        store=True,
    )
    account_manager = fields.Many2one(
        comodel_name="res.users",
        related="order_id.account_manager_id",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_company_id",
        store=True,
    )
    sale_order_company_id = fields.Many2one(
        comodel_name="res.company",
        related="order_id.company_id",
    )
    sale_blanket_order_company_id = fields.Many2one(
        comodel_name="res.company",
        related="blanket_order_id.company_id",
    )
    amount = fields.Monetary(
        string="Booking Amount",
        currency_field="currency_id",
        required=True,
        readonly=True,
    )
    amount_untaxed = fields.Monetary(
        string="Booking Amount Untaxed",
        currency_field="currency_id",
        required=True,
        readonly=True,
    )
    order_amount_total = fields.Monetary(
        string="Total Amount",
        readonly=True,
        currency_field="currency_id",
        required=True,
    )
    order_amount_total_untaxed = fields.Monetary(
        string="Total Amount Untaxed",
        readonly=True,
        currency_field="currency_id",
        required=True,
    )
    order_prev_amount_total = fields.Monetary(
        string="Previous Total Amount",
        currency_field="currency_id",
        readonly=True,
    )
    order_prev_amount_total_untaxed = fields.Monetary(
        string="Previous Total Amount Untaxed",
        currency_field="currency_id",
        readonly=True,
    )
    tax_amount = fields.Float(
        string="Tax Amount",
        digits="Sale Price",
    )
    prev_tax_amount = fields.Float(
        string="Previous Tax Amount",
        digits="Sale Price",
    )
    order_detailed_state = fields.Char(
        string="Order Detailed Status On Booking",
        readonly=True,
    )
    chatter_entry_date = fields.Datetime(
        string="Chatter Entry Date",
        copy=False,
        default=lambda self: fields.Datetime.now(),
    )
    booking_line_ids = fields.One2many(
        string="Booking Lines",
        comodel_name="sale.booking.line",
        inverse_name="booking_id",
    )

    # END  ###
    # METHODS ###

    @api.depends(
        "order_id",
        "order_id.name",
        "blanket_order_id",
        "blanket_order_id.name",
    )
    def _compute_origin(self):
        """Sets the origin field based on Sale Order or Blanket Order."""
        for record in self:
            if record.order_id:
                record.origin = record.order_id.name
            elif record.blanket_order_id:
                record.origin = record.blanket_order_id.name
            else:
                record.origin = False

    @api.depends(
        "sale_order_currency_id",
        "sale_blanket_order_currency_id",
    )
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = (
                record.sale_order_currency_id.id
                or record.sale_blanket_order_currency_id.id
                or False
            )

    @api.depends(
        "sale_order_company_id",
        "sale_blanket_order_company_id",
    )
    def _compute_company_id(self):
        for record in self:
            record.company_id = (
                record.sale_order_company_id.id
                or record.sale_blanket_order_company_id.id
                or False
            )

    def add_new_entry(self, order=False, blanket_order=False, force=False):

        if order:
            order.ensure_one()
        if blanket_order:
            blanket_order.ensure_one()

        # If we did not receive booking values we extract it from the given Order
        booking_values = {
            "create_date": datetime.now(),
            "order_amount_total": (
                order.amount_total
                if order
                else (blanket_order.remaining_amount_total if blanket_order else 0)
            ),
            "order_amount_total_untaxed": (
                order.amount_untaxed
                if order
                else (blanket_order.remaining_amount_untaxed if blanket_order else 0)
            ),
            "order_detailed_state": (
                order.state
                if order
                else (blanket_order.state if blanket_order else None)
            ),
            "order_id": order.id if order else None,
            "blanket_order_id": blanket_order.id if blanket_order else None,
            "tax_amount": (
                order.amount_tax
                if order
                else (blanket_order.remaining_amount_tax if blanket_order else 0)
            ),
        }

        # Find the last booking entry if there is any
        last_booking_entry = self.get_last_booking_entry(order, blanket_order)

        if not force and not self.new_booking_needed(
            order, booking_values, last_booking_entry
        ):
            return False

        # Set previous amount total based on booking records or False
        self.set_previous_amount_totals(
            booking_values=booking_values, last_booking_entry=last_booking_entry
        )

        # Set some local variables for easier use
        order_amount_total = booking_values.get("order_amount_total")
        order_amount_total_untaxed = booking_values.get("order_amount_total_untaxed")
        order_prev_amount_total = booking_values.get("order_prev_amount_total")
        order_prev_amount_total_untaxed = booking_values.get(
            "order_prev_amount_total_untaxed"
        )
        is_cancel = (order and order.state == "cancel") or (
            blanket_order and blanket_order.state == "expired"
        )

        if last_booking_entry:
            # If we found previous entries we need the delta value
            booking_values.update(
                {
                    "amount": order_amount_total - order_prev_amount_total,
                    "amount_untaxed": order_amount_total_untaxed
                    - order_prev_amount_total_untaxed,
                }
            )
        else:
            # If no previous values are provided we will use the orders current amounts
            booking_values.update(
                {
                    "amount": order_amount_total,
                    "amount_untaxed": order_amount_total_untaxed,
                }
            )

        if is_cancel:
            if (
                not last_booking_entry
                or last_booking_entry
                and last_booking_entry.order_detailed_state == "cancel"
            ):
                # If we didn't find any previous booking entry
                # or the last entry was also for a cancel state
                # we don't wan't a new `cancel` state entry
                return False

            # If the order was canceled we need the
            # whole current amount total as negative
            # and set the order amounts to 0
            booking_values.update(
                {
                    "amount": order_amount_total * -1,
                    "amount_untaxed": order_amount_total_untaxed * -1,
                    "order_amount_total": 0,
                    "order_amount_total_untaxed": 0,
                }
            )

        # Round amount and amount_untaxed values just before creating sale booking
        digits = self.env["decimal.precision"].precision_get("Product Price")
        fields_to_round = [
            "amount",
            "amount_untaxed",
            "order_amount_total",
            "order_amount_total_untaxed",
            "order_prev_amount_total",
            "order_prev_amount_total_untaxed",
        ]
        for field in fields_to_round:
            booking_values[field] = float_round(booking_values.get(field, 0), digits)

        # Create the booking
        booking = self.env["sale.booking"].create(booking_values)
        booking.create_booking_lines(order, blanket_order)

        return booking

    def new_booking_needed(self, order, booking_values, last_booking_entry):
        """
        Check if we need to add a new Sale Booking Entry
        """

        if order and order.state == "cancel":
            # We always want to add a new booking entry if the Sale Order is canceled
            return True

        if self.is_quote_related_state(booking_values):
            # The Sale order is still in a Quote state
            return False

        if not last_booking_entry:
            # If this would be the first Sale Booking
            return True

        previous_values = last_booking_entry.read(list(booking_values.keys()))[0]

        fields_to_compare = [
            "order_amount_total",
            "order_amount_total_untaxed",
            "tax_amount",
        ]
        if all(
            float_compare(
                previous_values.get(field, 0),  # Ensure it doesn't throw a KeyError
                booking_values.get(field, 0),  # Default to 0 if missing
                precision_digits=4,
            )
            == 0
            for field in fields_to_compare
        ):
            return False
        return True

    def set_previous_amount_totals(self, booking_values, last_booking_entry):
        """
        Get the previous booking entry if there is any
        and set the previous field values based on that
        :return:
        """

        booking_values.update(
            {
                "order_prev_amount_total": last_booking_entry
                and last_booking_entry.order_amount_total
                or 0,
                "order_prev_amount_total_untaxed": last_booking_entry
                and last_booking_entry.order_amount_total_untaxed
                or 0,
                "prev_tax_amount": last_booking_entry
                and last_booking_entry.tax_amount
                or 0,
            }
        )

    def is_quote_related_state(self, booking_values):
        # Check if the provided state is related to a Quote or a Sale order
        order_detailed_state = booking_values.get(
            "order_detailed_state"
        ) or booking_values.get("blanket_order_detailed_state")
        if not order_detailed_state or order_detailed_state in [
            "draft",
            "sent",
        ]:
            return True

        return False

    def get_last_booking_entry(self, order=False, blanket_order=False):
        """Try to get the last booking entry"""
        if order:
            return self.search([("order_id", "=", order.id)], limit=1, order="id desc")
        if blanket_order:
            return self.search(
                [("blanket_order_id", "=", blanket_order.id)],
                limit=1,
                order="id desc",
            )

    def get_last_booking_line_entry(self, booking_line=False):
        """Try to get the last booking line entry"""
        if booking_line.sale_order_line_id:
            return self.env["sale.booking.line"].search(
                [
                    ("sale_order_line_id", "=", booking_line.sale_order_line_id),
                    ("id", "!=", booking_line.id),
                ],
                limit=1,
                order="id desc",
            )
        if booking_line.sale_blanket_order_line_id:
            return self.env["sale.booking.line"].search(
                [
                    (
                        "sale_blanket_order_line_id",
                        "=",
                        booking_line.sale_blanket_order_line_id,
                    ),
                    ("id", "!=", booking_line.id),
                ],
                limit=1,
                order="id desc",
            )

    def create_booking_lines(self, order=False, blanket_order=False):
        """
        Create the related Sale Booking Line records
        """
        if order:
            for order_line in order.order_line:
                booking_line_values = self.get_booking_line_values(
                    sale_order_line=order_line
                )
                new_line = self.env["sale.booking.line"].create(booking_line_values)
                previous_line = self.get_last_booking_line_entry(new_line)
                new_line_dict = {}
                if previous_line:
                    prev_qty = previous_line.product_uom_qty
                    qty_change = new_line.product_uom_qty - prev_qty
                    prev_price_total = previous_line.price_total
                    prev_price_subtotal = previous_line.price_subtotal
                    line_amount = new_line.price_total - previous_line.price_total
                    line_amount_untaxed = new_line.price_subtotal - previous_line.price_subtotal
                    if previous_line.booking_id.order_detailed_state == "cancel":
                        prev_qty = 0
                        qty_change = new_line.product_uom_qty
                        prev_price_subtotal = 0
                        prev_price_total = 0
                        line_amount = new_line.price_total
                        line_amount_untaxed = new_line.price_subtotal
                    
                    new_line_dict.update({
                        "prev_qty": prev_qty,
                        "qty_change": qty_change,
                        "prev_price_total": prev_price_total,
                        "prev_price_subtotal": prev_price_subtotal,
                        "prev_price_tax": previous_line.price_tax,
                        "line_amount": line_amount,
                        "line_amount_untaxed": line_amount_untaxed,
                    })
                    new_line.write(new_line_dict)
                    if previous_line.sale_order_id.state == 'cancel':
                        qty_change = -new_line.product_uom_qty
                        line_amount = new_line.price_total * -1
                        line_amount_untaxed = new_line.price_subtotal * -1
                        new_line.write({
                            "qty_change": qty_change,
                            "line_amount": line_amount,
                            "line_amount_untaxed": line_amount_untaxed,
                        })
                if new_line and not previous_line:
                    new_line.write({"prev_qty":0,"qty_change":new_line.product_uom_qty,"prev_price_total":0.0,"prev_price_subtotal":0})

        if blanket_order:
            for blanket_order_line in blanket_order.line_ids:
                booking_line_values = self.get_booking_line_values(
                    sale_blanket_order_line=blanket_order_line
                )
                new_line = self.env["sale.booking.line"].create(booking_line_values)
                previous_line = self.get_last_booking_line_entry(new_line)
                new_line_dict = {}
                if previous_line:
                    prev_qty = previous_line.product_uom_qty
                    qty_change = new_line.product_uom_qty - prev_qty
                    new_line_dict.update({
                        "prev_qty": prev_qty,
                        "qty_change": qty_change,
                        "prev_price_total": previous_line.price_total,
                        "prev_price_subtotal": previous_line.price_subtotal,
                        "prev_price_tax": previous_line.price_tax,
                        "line_amount": new_line.price_total - previous_line.price_total,
                        "line_amount_untaxed": new_line.price_subtotal - previous_line.price_subtotal,
                    })
                    new_line.write(new_line_dict)
                    if previous_line.sale_blanket_order_id.state == 'expired':
                        qty_change = -new_line.product_uom_qty
                        line_amount = -(new_line.price_total - previous_line.price_total)
                        line_amount_untaxed = -(new_line.price_subtotal - previous_line.price_subtotal)
                        new_line.write({
                            "qty_change": qty_change,
                            "line_amount": line_amount,
                            "line_amount_untaxed": line_amount_untaxed,
                        })
                if new_line and not previous_line:
                    new_line.write({"prev_qty":0,"qty_change":new_line.product_uom_qty,"prev_price_total":0.0,"prev_price_subtotal":0})

    def get_booking_line_values(
        self,
        sale_order_line=False,
        sale_blanket_order_line=False,
    ):
        """
        Get the values needed to create a Sale Booking Line record
        """

        # Get the Sale Order Line's Product's default price
        if sale_order_line:
            if (
                sale_order_line.order_id.pricelist_id
                and sale_order_line.order_id.partner_id
            ):
                original_price_unit = self.env[
                    "account.tax"
                ]._fix_tax_included_price_company(
                    sale_order_line._get_display_price(),
                    sale_order_line.product_id.taxes_id,
                    sale_order_line.tax_id,
                    sale_order_line.company_id,
                )
            else:
                original_price_unit = None

            # Set the base relation values
            return {
                "booking_id": self.id,
                "sale_order_id": self.order_id.id,
                "sale_order_line_id": sale_order_line.id,
                "name": sale_order_line.name,
                "invoice_lines": sale_order_line.invoice_lines.ids,
                "invoice_status": sale_order_line.invoice_status,
                "price_unit": sale_order_line.price_unit,
                "original_price_unit": original_price_unit,
                "product_lst_price": sale_order_line.product_id.lst_price,
                "price_subtotal": sale_order_line.price_subtotal,
                "price_tax": sale_order_line.price_tax,
                "price_total": sale_order_line.price_total,
                "tax_id": sale_order_line.tax_id.ids,
                "product_id": sale_order_line.product_id.id,
                "product_uom_qty": sale_order_line.product_uom_qty,
                "product_uom": sale_order_line.product_uom.id,
                "is_delivery": sale_order_line.is_delivery,
                "product_qty": sale_order_line.product_qty,
                "prev_qty": sale_order_line.product_uom_qty,
                "qty_change": 0,
                "prev_price_total": sale_order_line.price_total,
                "prev_price_subtotal": sale_order_line.price_subtotal,
                "prev_price_tax": sale_order_line.price_tax,
                "line_amount": sale_order_line.price_total,
                "line_amount_untaxed": sale_order_line.price_subtotal,
            }
        if sale_blanket_order_line:
            # Get the Sale Blanket Order Line's Product's default price
            if (
                sale_blanket_order_line.order_id.pricelist_id
                and sale_blanket_order_line.order_id.partner_id
            ):
                original_price_unit = self.env[
                    "account.tax"
                ]._fix_tax_included_price_company(
                    sale_blanket_order_line._get_display_price(),
                    sale_blanket_order_line.product_id.taxes_id,
                    sale_blanket_order_line.taxes_id,
                    sale_blanket_order_line.company_id,
                )
            else:
                original_price_unit = None

            # Set the base relation values
            return {
                "booking_id": self.id,
                "sale_blanket_order_id": self.blanket_order_id.id,
                "sale_blanket_order_line_id": sale_blanket_order_line.id,
                "name": sale_blanket_order_line.name,
                "price_unit": sale_blanket_order_line.price_unit,
                "original_price_unit": original_price_unit,
                "product_lst_price": sale_blanket_order_line.product_id.lst_price,
                "price_subtotal": sale_blanket_order_line.remaining_price_subtotal,
                "price_tax": sale_blanket_order_line.remaining_price_tax,
                "price_total": sale_blanket_order_line.remaining_price_total,
                "tax_id": sale_blanket_order_line.taxes_id.ids,
                "product_id": sale_blanket_order_line.product_id.id,
                "product_uom_qty": sale_blanket_order_line.remaining_uom_qty,
                "product_uom": sale_blanket_order_line.product_uom.id,
                "product_qty": sale_blanket_order_line.ordered_uom_qty,
                "prev_qty": sale_blanket_order_line.remaining_uom_qty,
                "qty_change": 0,
                "prev_price_total": sale_blanket_order_line.price_total,
                "prev_price_subtotal": sale_blanket_order_line.price_subtotal,
                "prev_price_tax": sale_blanket_order_line.price_tax,
                "line_amount": sale_blanket_order_line.price_total,
                "line_amount_untaxed": sale_blanket_order_line.price_subtotal,
            }

    # END #######
