# Import Python libs
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import models, fields
from odoo.addons.ol_delivery.models.tools import get_product_data_from_order_lines_data


class SaleOrder(models.Model):
    """
    Delivery related additions to the Sale Order Model
    """

    _inherit = "sale.order"

    # COLUMNS #######
    manual_delivery_price = fields.Float(
        string="Manual Delivery Price",
        digits="Product Price",
        copy=False,
        default=None,
        help="This is the manual delivery price that you can set for this order, the `Delivery Price Calculation Type` must be set to `Manual` for this to be used.",
    )
    delivery_price_type = fields.Selection(
        selection=[("manual", "Manual"), ("automatic", "Automatic")],
        string="Delivery Price Calculation Type",
        default="automatic",
        copy=False,
        help="This controls if we use the Delivery Carrier automatic price calculation or a "
        "manual one that you set here.",
    )
    delivery_override_reason = fields.Text(string="Override Reason", copy=False)
    delivery_account_number = fields.Char(string="Delivery Account Number", copy=False)
    delivery_notes = fields.Text(string="Delivery Notes", copy=False, tracking=True)
    general_notes = fields.Text(string="General Notes", copy=False)
    # END COLUMNS ###

    def copy(self, default=None):

        # First, let the original copy method duplicate the Sale Order
        new_sale_order = super().copy(default)

        if not new_sale_order.carrier_id.active:
            # If the Sale Order is using an archived carrier remove the related delivery line
            order_lines_to_remove = new_sale_order.order_line.filtered(
                lambda line: line.is_delivery
            )
            _logger.info(
                f"DELIVERY | Removed delivery line for `{new_sale_order.carrier_id.name} ({new_sale_order.carrier_id.id})` from Sale Order: `{new_sale_order.name} ({new_sale_order.id})`"
            )
            order_lines_to_remove.unlink()

        return new_sale_order

    def get_product_data_from_sale_order(self):
        """
        Get the OnLogic specific product data from the sale order lines.
        """
        order_lines_data = []
        for order_line in self.order_line:
            if order_line.is_delivery:
                continue
            order_lines_data.append(
                {
                    "price_unit": order_line.price_unit or 0.0,
                    "qty": order_line.product_uom_qty or None,
                    "product_id": order_line.product_id.uuid or None,
                    "configuration": order_line.get_configuration(),
                }
            )
        return get_product_data_from_order_lines_data(
            env=self.env, company=self.company_id, order_lines_data=order_lines_data
        )

    def _get_estimated_weight(self):
        """
        Use the custom OnLogic method to get the weight of the order.
        This won't return an estimation but an exact weight based on the product.
        In case of a system the exact weight of the components.
        """
        try:
            product_data = self.get_product_data_from_sale_order()
            return product_data.get("total_weight") or 0.0
        except Exception as e:
            _logger.exception(
                f"DELIVERY | Error during `_get_estimated_weight` could not use `get_product_data_from_sale_order`, falling back to super | Error {e}"
            )
            return super()._get_estimated_weight()

    def set_delivery_line(self, carrier, amount):
        """
        Ensure that we keep certain Sale Order fields when the deliver line gets deleted.

        In core the `set_delivery_line` calls the `_remove_delivery_line` method which in return
        resets some sale order fields (fields_to_save). This happens as a result of our own code
        in ls_delivery_wizard.models.sale.SaleOrderLine.unlink() which is good, but we don't want
        to do it when the User clicks the `Update` button in the Delivery Wizard.
        """
        fields_to_save = self.get_delivery_fields_to_save()
        order_data = defaultdict(dict)
        order_original_data = defaultdict(dict)
        for order in self:
            for field in fields_to_save:
                order_data[order.id][field] = getattr(order, field)

            order_original_data[order.id].update(
                {
                    "carrier_id": order.carrier_id and order.carrier_id.id or "",
                    "carrier_name": order.carrier_id
                    and order.carrier_id.display_name
                    or "",
                    "delivery_price": sum(
                        order.order_line.filtered(lambda l: l.is_delivery).mapped(
                            "price_unit"
                        )
                    ),
                }
            )

        res = super(SaleOrder, self).set_delivery_line(carrier, amount)

        for order in self:
            order.write(order_data[order.id])
            order.add_delivery_change_msg(order_original_data)

        return res

    def get_delivery_fields_to_save(self):
        """
        Sale Order fields we want to keep when the deliver line gets deleted.
        """
        return [
            "manual_delivery_price",
            "delivery_price_type",
            "delivery_override_reason",
            "delivery_account_number",
        ]

    def create_new_delivery_change_msg(self, values, price):
        """
        Check if we should add a new delivery change message
        """
        self.ensure_one()

        if (
            (values.get("carrier_id") != self.carrier_id.id)
            or (values.get("delivery_price") != price)
            or (values.get("delivery_account_number") != self.delivery_account_number)
        ):
            return True

        return False

    def get_delivery_message_body(self, values, price):
        """
        Assemble the message
        """
        msg_body = ""

        display_name = self.carrier_id.display_name
        carrier_name = values.get("carrier_name")
        if carrier_name == display_name:
            msg_body += f"<li>Delivery Method: {display_name}</li>"
        else:
            msg_body += (
                f"<li>Delivery Method: {carrier_name} &#8594; {display_name}</li>"
            )

        delivery_price = values.get("delivery_price")
        if delivery_price == price:
            msg_body += f"<li>Delivery Price: {delivery_price}</li>"
        else:
            msg_body += f"<li>Delivery Price: {delivery_price} &#8594; {price}</li>"

        msg_body += f"<li>Delivery Price Type: {self.delivery_price_type.title()}</li>"

        if self.delivery_override_reason:
            msg_body += f"<li>Override Reason: {self.delivery_override_reason}</li>"

        account_num = self.delivery_account_number or ""
        if account_num:
            msg_body += f"<li>Delivery Account Number: {account_num}</li>"

        return msg_body

    def add_delivery_change_msg(self, original_order_values):
        """
        Add a chatter entry to the order if any important Deliver information changed
        :param original_order_values: The Sale Order values before the delivery_set() function run
        :return: Boolean
        """

        self.ensure_one()

        if self.env.context.get("skip_order_delivery_chatter", False):
            return False

        delivery_price = sum(
            self.order_line.filtered(lambda l: l.is_delivery).mapped("price_unit")
        )

        if self.create_new_delivery_change_msg(
            values=original_order_values, price=delivery_price
        ):
            msg = "<h5>Delivery Data updated</h5>"
            msg += "<ul>"
            msg += self.get_delivery_message_body(
                values=original_order_values, price=delivery_price
            )
            msg += f"<li>Changed by: {self.env.user.name}</li>"
            msg += "</ul>"
            self.message_post(body=msg)

            return True

        return False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        """
        If the delivery line gets removed make sure we reset the related values on the Sale Order
        """
        for line in self:
            if line.is_delivery:
                unlink_data = self.get_sale_order_delivery_reset_values()
                line.order_id.write(unlink_data)
        return super(SaleOrderLine, self).unlink()

    def get_sale_order_delivery_reset_values(self):
        """
        Data we want to write to the related Sale Order
        """
        return {
            "manual_delivery_price": None,
            "delivery_price_type": "automatic",
            "delivery_override_reason": None,
            "delivery_account_number": None,
        }
