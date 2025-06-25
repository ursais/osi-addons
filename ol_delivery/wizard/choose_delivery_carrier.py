# Import Odoo libs
from odoo import fields, models, api
from odoo.exceptions import UserError


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    # COLUMNS #######
    delivery_price_type = fields.Selection(
        string="Calculation Type", related="order_id.delivery_price_type", readonly=False, required=True
    )
    delivery_notes = fields.Text(related="order_id.delivery_notes", readonly=False)
    manual_delivery_price = fields.Float(related="order_id.manual_delivery_price", readonly=False)
    delivery_override_reason = fields.Text(related="order_id.delivery_override_reason", readonly=False)
    delivery_account_number = fields.Char(related="order_id.delivery_account_number", readonly=False)
    delivery_account_required = fields.Boolean(related="carrier_id.account_required", readonly=True)
    sale_order_state = fields.Selection(string="Sale Order Sate", related='order_id.state')
    # END COLUMNS ###

    def _get_shipment_rate(self):
        """
        Hijack the wizard confirm function to handle the manual delivery price type event
        """

        if self and self.order_id.delivery_price_type == "manual":
            # If the delivery price type is manual
            # we don't need to trigger the automatic carrier price recalculation
            # We save a few seconds of load time with this
            return {"no_rate": False}

        return super(ChooseDeliveryCarrier, self)._get_shipment_rate()

    def button_confirm(self):
        """
        Hijack the wizard confirm function to handle the manual delivery price type event
        """
        if self.delivery_price_type == "manual":
            # If the type is manual we need to override the automatically calculated price
            self.delivery_price = self.manual_delivery_price
            self.delivery_message = self.delivery_override_reason
        else:
            # If the type is automatic we want to reset some fields
            self.order_id.write(
                {
                    "manual_delivery_price": None,
                    "delivery_override_reason": None,
                }
            )

        # Continue with the core workflow
        return super(ChooseDeliveryCarrier, self).button_confirm()
