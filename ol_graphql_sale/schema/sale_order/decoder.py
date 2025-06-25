# Import Python Libs

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder


class SaleOrderDecoder(BaseDecoder):
    # Direct field translations
    decode_amount_tax = "ecommerce_tax"
    decode_amount_total = "ecommerce_total"

    def decode_locale(self, message_field, message_value):
        self.add_post_graphql_create_parameter(message_field, message_value)

    def decode_state(self, message_field, message_value):
        self.add_post_graphql_create_parameter(message_field, message_value)

    def decode_tax_exemption_code(self, _, message_value):
        if not message_value:
            return self.add_decoded_data(values={"exemption_code_id": False})

        matched_codes = self.env["exemption.code"].search(
            [("code", "=", message_value)], limit=1
        )

        if matched_codes:
            return self.add_decoded_data(
                values={
                    "exemption_code_id": matched_codes.id if matched_codes else False
                }
            )

    def decode_tax_exemption_number(self, _, message_value):
        return self.add_decoded_data(values={"exemption_code": message_value or False})

    def decode_shipping_method(self, _, message_value):
        """
        Translate shipping carrier methods
        """
        if not message_value:
            self.raise_ackable_exception("No shipping method provided in the message")

        delivery_sale_line_values = False
        delivery_values = self.find_delivery_carrier(message_value)
        # only add a sale line if there's a product id we can set it for
        if delivery_values and delivery_values.get("product_id"):
            # move some fields from the delivery_values and into delivery_sale_line_values
            delivery_sale_line_values = {
                "is_delivery": True,
                "product_uom": 1,
                "price_unit": message_value.get("price", 0.0),
                "product_uom_qty": delivery_values.pop("product_uom_qty", 1),
                "product_id": delivery_values.pop(
                    "product_id", False
                ),  # this is the product_id of the shipping line item (not component product)
            }
            # Mark the sale order as using Manual delivery prices
            # this ensures that we keep the delivery cost calculated by Commercetools unchanged
            delivery_values.update(
                {
                    "manual_delivery_price": message_value.get("price", 0.0),
                    "delivery_price_type": "manual",
                }
            )

        # if we have shipping line items in the SO, update the order_line field
        # (we have force decoded shipping_method in the SO mutator, so these will
        # be added to order_line before order_line itself is decoded)
        if delivery_sale_line_values:
            sale_lines = self.data.get("order_line", [])
            sale_lines.append(delivery_sale_line_values)
            self.data["order_line"] = sale_lines

        if delivery_values:
            return self.add_decoded_data(values=delivery_values)

    def decode_order_line(self, _, message_value):
        """
        Handle message decoding of the sale order lines
        """
        if not message_value:
            self.log_warning_message("No order lines in the message")
            return self.add_decoded_data({"order_line": False})

        self.odoo_data.add_action(
            odoo_record=self.odoo_record,
            function="_post_graphql_process_order_lines",
            function_kwargs={"order_lines": message_value},
            uuid=self.uuid,
        )

    def decode_po_number(self, _, message_value):
        """
        Translate PO Number (website) to Customer Reference (Odoo)
        """
        return self.add_decoded_data(
            values={"client_order_ref": message_value or False}
        )

    def find_delivery_carrier(self, message_value):
        """
        Decide which type of carrier should decode this message
        and apply holds if necessary, when we lack information
        """
        service_uuid = message_value.get("uuid")

        # if we aren't provided any of the information we need to identify the carrier, apply a hold
        if not service_uuid:
            self.log_warning_message(
                f"No carrier UUID provided, exceptions will be applied"
            )
            # TODO: Make sure that exceptions are triggered when this condition is met
            return

        delivery_method = self.env["delivery.carrier"].search(
            [("uuid", "=", message_value.get("uuid"))]
        )

        if delivery_method:
            self.log_mutation_message(
                f"Found matching delivery method(s) {delivery_method}"
            )

            return {
                "carrier_id": delivery_method[0].id,
                "product_id": delivery_method.product_id.id,  # the "product_id" refers to the "product" that is the shipping item and not a component "product"
                "product_uom_qty": 1,
            }

        self.log_warning_message(
            f"No matching delivery method found for carrier with UUID: {service_uuid}, exceptions will be applied"
        )
        # TODO: Make sure that exceptions are triggered when this condition is met
