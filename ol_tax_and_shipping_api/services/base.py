# Import Python Libs
from graphql import GraphQLError

# Import Odoo Libs
from odoo import models, _

# Error codes are logged in this sheet: https://docs.google.com/spreadsheets/d/1uUxYRB9ll56pamWJMofQa4HpgC6QESglk4FZfMI3otU/edit?usp=sharing
# TTV uses this sheet for messaging elements based on error codes on the front-end


class TSBaseService(models.AbstractModel):
    _name = "ts.base.service"
    _description = "Tax and Shipping Base service"

    def get_company(self, data):
        """
        Get the Odoo company from the request
        """
        company_string = data.get("onlogic_company", False)

        if not company_string:
            raise GraphQLError("Err 001: TS API |: OnLogic Company set not set!")

        # Try to find the related companies
        company = self.env["res.company"].sudo().search([("short_name", "=", company_string.lower())])

        if not company:
            raise GraphQLError(f"Err 002: TS API |: Incorrect `onlogic_company`: {company_string}")

        return company

    def get_sale_order(self, data, company, add_deliver_line=False):
        """
        Create a pseudo Sale Order to be able to trigger correct shipping calculations
        """

        # Get customer from the request if possible
        customer = self.env["res.partner"].get_by_uuid(data.get("customer_id", None))

        # Get the delivery address
        delivery_partner = self.get_delivery_address(data)

        delivery_carrier = delivery_price = delivery_sale_line = False
        consumer_type = data.get("consumer_type", False)

        if add_deliver_line:
            delivery_carrier, delivery_price, delivery_sale_line = self.get_delivery_carrier_data(
                data, company
            )

        # Get the language or default to US english
        language = data.get("locale", "en_US")

        sale_order_values = {
            # It is important that the Sale Order name is less than 50 characters
            # as the AVATAX API doesn't accept anything longer than that
            # Check: `ls_tax_and_shipping_api/models/gql_base_interface.py _adjust_code()`
            "name": f"T&S-{data.get('name', '')}"[0:50],
            "state": "draft",
            # TODO: `detailed_state` field is missing
            # 'detailed_state': 'draft',
            "company_id": company.id,
            "partner_id": (
                customer.id if customer else delivery_partner.id
            ),  # if customer uuid provided, use found res_partner record for sales order
            "partner_shipping_id": delivery_partner.id,
            "partner_invoice_id": delivery_partner.id,
            # 'lang': language,
            # 'communication_language': language,
            # 'origin_system': "TAX & Shipping API"
        }

        # TODO: `consumer_type` field is missing
        # if consumer_type and consumer_type in [
        #     x[0] for x in self.env['sale.order']._fields.get('consumer_type').selection
        # ]:
        #     # If Consumer Type is set, and is a valid value
        #     sale_order_values.update({'consumer_type': consumer_type})

        if delivery_carrier:
            sale_order_values.update(
                {
                    "carrier_id": delivery_carrier.id,
                    # 'manual_delivery_price': delivery_price,
                    # 'delivery_price_type': 'manual',
                }
            )

        # We use `new` rather than `create` this is much faster
        # and if not specifically requested won't persist the record in the database
        sale_order = self.env["sale.order"].new(
            values=sale_order_values,
            ref="tax_and_shipping_pseudo_sale_order",
        )

        # Set the language for the Context
        self.env.context = self.with_context(
            lang=sale_order.partner_id.lang or self.env.context.lang
        ).env.context

        # Collect the Sale Order Line information
        for idx, order_line_data in enumerate(data.get("lines", [])):
            # sale_order_lines.append((0, 0, self.get_sale_order_line_values(line)))
            sale_order.order_line += self.get_sale_order_line(request_order_line_data=order_line_data, idx=idx)

        if delivery_sale_line:
            # Also add the delivery line
            sale_order.order_line += delivery_sale_line

        return sale_order

    def get_delivery_address(self, data):
        """
        Get the delivery address based on the request
        """

        delivery_data = data.get("shipping_address", {})

        if not delivery_data:
            raise GraphQLError(
                f"Err 003: TS API |: No `delivery address` data found request: {delivery_data}"
            )

        # Get the country
        delivery_country_code = delivery_data.get("country", False)
        if not isinstance(delivery_country_code, str):
            raise GraphQLError(
                "Err 004: TS API |: Invalid value for field Delivery Address country:"
                f" `{delivery_country_code}`. Should be a string!"
            )
        country_id = self.env["res.country"].search([("code", "=", delivery_country_code.upper())])

        # Get the state
        state_id = self.get_state_id(delivery_data, country_id)

        first_name = delivery_data.get("first_name", "")
        last_name = delivery_data.get("last_name", "")

        # We use `new` rather than `create` this is much faster
        # and if not specifically requested won't persist the record in the database
        return (
            self.env["res.partner"]
            .with_context(skip_webhooks=True)
            .new(
                values={
                    "name": f"{first_name} {last_name}",
                    "city": delivery_data.get("city", ""),
                    "street": delivery_data.get("street", ""),
                    "street2": delivery_data.get("street2", ""),
                    "zip": delivery_data.get("zip", ""),
                    "country_id": country_id.id,
                    "state_id": state_id.id,
                    "phone": delivery_data.get("phone", "ups api"),
                    "is_company": False,
                    "type": "other",
                    "vat": delivery_data.get("vat", False),
                },
                ref="tax_and_shipping_pseudo_partner",
            )
        )

    def get_state_id(self, delivery_data, country_id):
        delivery_state_code = delivery_data.get("state", False)

        if not delivery_state_code:
            return self.env["res.country.state"]

        # Try to find the related companies
        state_id = self.env["res.country.state"].search([("code", "=", delivery_state_code.upper())])

        if state_id and len(state_id) > 1 and country_id:
            # If we found more than one State, we need to filter down based on the country as well
            # Try to find the related companies
            state_id = state_id.filtered(lambda state: state.country_id.id == country_id.id)

        return state_id

    def get_sale_order_line(self, request_order_line_data, idx):
        """
        Get the values for the Sale Order Line
        IMPORTANT:  This is not getting the correct Product Variant!
                    We do not take the received configuration into account at all.
                    We do this to speed things up, all of the specific correct configuration based information
                    is retrieved and provided by the `get_system_data_from_message_order_lines()` method!
        """
        
        # Get the Product Template and related Variant
        uuid = request_order_line_data.get("product_id", False)
        product_template = self.env["product.template"].get_by_uuid(uuid)
        
        # This is NOT the correct product variant based in the configuration, read the method's doc above!
        product_product = product_template.product_variant_id
        if not product_product:
            product_product = self.env["product.product"].new({"product_tmpl_id": product_template.id})
        
        order_line_data = {
            "uuid": request_order_line_data.get("order_line_uuid"),
            "product_id": product_product.id,
            "product_uom_qty": request_order_line_data.get("qty") or 1.0,
            "product_uom": (
                product_template.uom_id.id
                if product_template.uom_id
                else self.env.ref("uom.product_uom_unit").id
            ),
            "price_unit": request_order_line_data.get("price_unit") or 0.0,
        }

        return self.env["sale.order.line"].new(
            values=order_line_data,
            ref=f"tax_and_shipping_pseudo_sale_order_line_{idx}",
        )

    def get_delivery_carrier_data(self, request, company):
        carrier_data = request.get("shipping_method", False)
        if not carrier_data:
            # Return empty recordset if no delivery data is present in the request
            return self.env["delivery.carrier"], None, self.env["sale.order.line"]

        uuid = carrier_data.get("uuid", False)
        if not uuid:
            raise GraphQLError("Err 006: TS API |: No Delivery Carrier UUID present `shipping_method` data!")

        carrier = self.env["delivery.carrier"].get_by_uuid(uuid)

        if not carrier:
            raise GraphQLError(f"Err 007: TS API |: Delivery Carrier uuid does not exist in Odoo!: `{uuid}`")

        if carrier.company_id and company.id != carrier.company_id.id:
            raise GraphQLError(
                f"Err 008: TS API |: Delivery Carrier not allowed in defined company `{carrier.name}`: `{company.short_name}`!"
            )

        price = carrier_data.get("price", False)

        if price is False or price is None:
            raise GraphQLError(
                f"Err 009: TS API |: Price not provided for Delivery Carrier `{carrier.name}`!"
            )

        delivery_sale_line = self.env["sale.order.line"].new(
            values={
                "is_delivery": True,
                "product_uom": 1,
                "price_unit": price,
                "product_uom_qty": 1,
                "product_id": carrier.product_id.id,
                "uuid": str(carrier.product_id.uuid),
            },
            ref="tax_and_shipping_pseudo_sale_order_line_delivery",
        )
        # Mark the sale order as using Manual delivery prices
        # this ensures that we keep the delivery cost

        return carrier, price, delivery_sale_line
