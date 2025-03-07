# Import Odoo libs
from odoo import fields, models, api


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    # COLUMNS ###

    booking_ids = fields.One2many(
        comodel_name="sale.booking",
        inverse_name="blanket_order_id",
        string="All Bookings",
    )
    remaining_amount_untaxed = fields.Monetary(
        string="Remaining Untaxed Amount",
        store=True,
        readonly=True,
        compute="_compute_remaining_amount_all",
        tracking=True,
    )
    remaining_amount_tax = fields.Monetary(
        string="Remaining Taxes",
        store=True,
        readonly=True,
        compute="_compute_remaining_amount_all",
    )
    remaining_amount_total = fields.Monetary(
        string="Remaining Total",
        store=True,
        readonly=True,
        compute="_compute_remaining_amount_all",
    )

    # END #######
    # METHODS ###

    @api.depends("line_ids.remaining_price_total")
    def _compute_remaining_amount_all(self):
        for order in self.filtered("currency_id"):
            remaining_amount_untaxed = remaining_amount_tax = 0.0
            for line in order.line_ids:
                remaining_amount_untaxed += line.remaining_price_subtotal
                remaining_amount_tax += line.remaining_price_tax
            order.update(
                {
                    "remaining_amount_untaxed": order.currency_id.round(
                        remaining_amount_untaxed
                    ),
                    "remaining_amount_tax": order.currency_id.round(
                        remaining_amount_tax
                    ),
                    "remaining_amount_total": remaining_amount_untaxed
                    + remaining_amount_tax,
                }
            )

    def get_booking_trigger_fields(self):
        """
        Fields that should trigger Sale Booking creation if they are found in the write values
        """
        return [
            "remaining_amount_total",
            "remaining_amount_untaxed",
            "remaining_amount_tax",
            "state",
        ]

    def write(self, vals):
        """
        Hook into the write method to trigger sale booking creation
        """

        res = super().write(vals)

        trigger_fields = self.get_booking_trigger_fields()

        if any(key in trigger_fields for key in vals.keys()):
            # If any of the fields appears in the Order vals
            # we need to check if a new booking entry is necessary
            self.sale_blanket_booking_trigger()

        return res

    @api.depends(
        "remaining_amount_untaxed",
        "remaining_amount_total",
        "remaining_amount_tax",
    )
    def _amount_all(self):
        """
        Trigger Sale Booking related functionality if the Sale Order's amounts change
        """
        super()._amount_all()
        self.sale_blanket_booking_trigger()

    def sale_blanket_booking_trigger(self, force=False):
        """Add a new booking entry if necessary"""

        booking_object = self.env["sale.booking"]

        for order in self:
            booking_object.add_new_entry(blanket_order=order, force=force)

    # END #######
