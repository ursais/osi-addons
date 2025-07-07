from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # COLUMNS ###

    booking_ids = fields.One2many(
        comodel_name="sale.booking",
        inverse_name="order_id",
        string="All Bookings",
    )

    # END #######
    # METHODS ###

    def get_booking_trigger_fields(self):
        """
        Fields that should trigger Sale Booking creation if they are found in the write values
        """
        return [
            "amount_total",
            "amount_untaxed",
            "amount_tax",
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
            self.sale_booking_trigger()
            # Also compute remaining amounts on blanket order lines
            self.order_line.blanket_order_line._compute_remaining_prices()

        return res

    def sale_booking_trigger(self, force=False):
        """Add a new booking entry if necessary"""

        booking_object = self.env["sale.booking"]

        for order in self:
            booking_object.add_new_entry(order=order, force=force)

    # END #######
