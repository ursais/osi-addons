# Import Python Libs
import re

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder


class ResPartnerDecoder(BaseDecoder):
    """
    This decoder handles all of the related res_partner records on a sale order i.e. partner_id, partner_invoice_id,
    and partner_shipping_id. There is a lot of logic, especially around the main partner, to find existing partners or
    create a placeholder so this is separated out to reduce clutter.
    """

    def decode_partner_and_addresses(self):
        """
        Force decode the partner and addresses before any other sale order processing
        """
        billing_message = self.data.pop("billing_address", False)
        billing_address = self.env["res.partner"]
        if not billing_message:
            self.log_mutation_message(
                f"No billing_address data provided. Using partner_id as the billing address"
            )
        else:
            billing_address = self.create_address(billing_message)

        shipping_message = self.data.pop("shipping_address", False)
        shipping_address = self.env["res.partner"]
        if not shipping_message:
            self.log_mutation_message(
                f"No shipping_address data provided. Using partner_id as the shipping address"
            )
        else:
            shipping_address = self.create_address(shipping_message)

        partner_message = self.data.pop("partner_id", False)
        if not partner_message:
            self.raise_ackable_exception("No partner_id data provided")
        # as long as we have something to work with, attempt to find the existing partner record
        partner = self.find_partner("partner_id", partner_message)
        if not partner:
            self.log_mutation_message(
                f"Creating a new placeholder partner for partner_id."
            )
            partner = self.create_placeholder_partner(
                "partner_id", partner_message, shipping_address, billing_address
            )
        # set customer group here instead of decoding later
        if self.data.get("is_guest", False) and (
            customer_group := self.data.get("customer_group", False)
        ):
            pricelist = self.env["product.pricelist"].search(
                [("uuid", "=", customer_group)], limit=1
            )
            if pricelist:
                partner.write({"property_product_pricelist": pricelist.id})

        # set the parents of the shipping and billing addresses
        if shipping_address:
            shipping_address.parent_id = partner.id
        if billing_address:
            billing_address.parent_id = partner.id

        values = {
            "partner_id": partner.id,
            "partner_invoice_id": billing_address.id or partner.id,
            "partner_shipping_id": shipping_address.id or partner.id,
        }

        return self.add_decoded_data(values=values)

    def create_address(self, message):
        # These fields are not sent by Commercetools, so we want to ignore them
        message.pop("tax_exemption_code", False)
        message.pop("tax_exemption_number", False)
        message.pop("company", False)

        # Commercetools will only send UUIDs on an address if the user saves the address but we don't want to use it.
        # Instead, we generate a new one each time and post the Commercetools one in a chatter message on the address.
        message_uuid = message.pop("uuid", False)

        decoded_vals = {
            "active": False,
            "origin_system": "COMMERCETOOLS",
        }

        decoded_vals["vat"] = self.sanitize_vat(
            message.get("vat", False), message.get("country_id", False)
        )

        country_id = self.env["res.country"].search(
            [("code", "=", message.get("country_id", "").upper())]
        )
        decoded_vals["country_id"] = country_id.id or False

        sanitized_state_id = self.sanitize_state_id(message.get("state_id", ""))
        state_id = self.env["res.country.state"].search(
            [("code", "=", sanitized_state_id.upper())]
        )
        if state_id and len(state_id) > 1 and decoded_vals.get("country_id", False):
            # If we found more than one State, we need to filter down based on the country as well
            state_id = state_id.filtered(
                lambda state: state.country_id.id == decoded_vals["country_id"]
            )
        decoded_vals["state_id"] = state_id.id

        address_type = message.get("type", "")
        if address_type != None:
            decoded_vals["type"] = address_type.lower()

        message.update(decoded_vals)

        address = self.env["res.partner"].create(message)

        # Keep track of the incoming Commercetools UUID by posting a chatter message to the address
        if message_uuid:
            address.message_post(body=f"Commercetools UUID: {message_uuid}")

        return address

    def sanitize_state_id(self, state_id):
        """
        We only want to accept ISO states
        """
        if not state_id:
            return ""

        if all([not x.isalnum() for x in state_id]) or len(state_id) > 3:
            self.log_warning_message(
                f"S:2 | Warning during Sale Order decoding. | Invalid address state_id: {state_id},"
                " setting to False",
                tid=self.transaction_id,
            )
            return ""

        return state_id

    def sanitize_vat(self, vat, country_id):
        """
        VAT should be alphanumeric
        """
        if not vat:
            return False

        vat = re.sub("[^A-Za-z0-9]", "", vat)
        if all([x.isdigit() for x in vat]):
            vat = country_id + vat

        return vat

    def find_partner(self, message_field, message_value):
        """
        Attempt to find pre-existing partner by given UUID; if no partner
        has current UUID, create a placeholder one with info provided
        """
        requested_uuid = message_value.get("uuid", False)
        partner_record = False
        if not requested_uuid:
            self.raise_ackable_exception(f"No UUID provided for {message_field}")
        else:
            partner_record = self.env["res.partner"].get_by_uuid(requested_uuid)

        if not partner_record.active:
            # If the Sale Order message is for an archived partner, make sure to un-archive it
            # We also allow this un-archive to send webhook triggers
            # We mainly do this so HubSpot can re-create this archived partner
            partner_record.with_context(
                webhook_skip_graphql_incoming_check=True
            ).toggle_active()

        # if we didn't find the partner by UUID try to get if via the email address
        if not partner_record or not partner_record.exists():
            # log an extra warning specifically for non-guests at this point, as we should have their UUID
            if not self.data.get("is_guest", False):
                self.log_warning_message(
                    f"Non-guest checkout for Sale Order {message_value.get('name', '')}"
                    f" but {message_field} with UUID: `{requested_uuid}` is not found in Odoo!"
                )

            self.log_warning_message(
                f"No partner found for {message_field} with UUID {requested_uuid}, falling back on email"
                f" instead: {message_value.get('email', False)}"
            )

            partner_record = self.find_partner_without_uuid(
                message_field, message_value
            )

        # Make sure we only have 1 partner
        if len(partner_record) > 1:
            self.raise_ackable_exception(
                f"More than one active partner found with UUID {requested_uuid}: {partner_record}"
            )

        return partner_record

    def create_placeholder_partner(
        self, message_field, partner_message, shipping_address, billing_address
    ):
        """
        If no existing partner has been found, create a placeholder

        The following logic only applies to partners, so if this method is called with anything other
        than the partner_id field we want to skip this logic.
        """

        if message_field != "partner_id":
            return False

        decoded_vals = {
            "origin_system": "COMMERCETOOLS",
            "type": "contact",
        }
        # Website orders will have partner UUID already assigned by Commercetools, make sure to keep it!
        if partner_message.get("uuid", False):
            decoded_vals["uuid"] = partner_message["uuid"]

        # TODO: Will there be a firstname/lastname field in odoo 17?
        for field in [
            "email",
            "name",
            # "firstname",
            # "lastname",
            "phone",
        ]:
            decoded_vals[field] = (
                partner_message.get(field, False)
                or getattr(shipping_address, field)
                or getattr(billing_address, field)
                or False
            )

        partner_name = partner_message.get("name", False)
        if partner_name:
            decoded_vals["name"] = partner_name
            # TODO: Will there be a firstname/lastname field in odoo 17?
            # split_name = partner_name.split(" ")
            # decoded_vals["firstname"] = split_name[0]
            # decoded_vals["lastname"] = " ".join(split_name[1:])

        decoded_vals["address_company_name"] = shipping_address.company_name or ""
        decoded_vals["company_name"] = shipping_address.company_name or ""

        return self.env["res.partner"].create_placeholder_record(
            decoded_vals,
            field_name=message_field,
            transaction_id=self.data.transaction_id,
            prioritize_defaults=True,
        )

    def find_partner_without_uuid(self, message_field, message_value):
        """
        Work through fallback logic if finding a partner via UUID isn't successful
        """
        empty_partner_record = self.env["res.partner"]
        email = message_value.get("email", False)
        if not email:
            self.log_warning_message(
                f"No email provided for {message_field} for guest checkout, will create placeholder instead"
            )
            return empty_partner_record

        # as long as we have an email, we continue to try...
        #    ...via the email address for the current company (OnLogic Store)
        #    ...via a cloned email address (it has its own formatting)
        tid = self.data.transaction_id
        partner = empty_partner_record.get_partner_by_email(email, tid)
        # TODO: we need to determine if we need to support searching for cloned email addresses in odoo 17.
        # Will there be cleanup that eliminates them?
        # or empty_partner_record.get_partner_by_email(
        #     empty_partner_record.get_cloned_email_address(email), tid
        # )

        # if we still don't have a partner at this point we can just return an empty recordset
        if not partner:
            self.log_warning_message(
                "Could not find existing address-type partner for guest checkout via UUID or email, will"
                " create placeholder instead"
            )
            return empty_partner_record

        # return the found Odoo record
        self.log_warning_message(
            f"For{' guest' if self.data.get('is_guest', False) else ''} Sale Order"
            f" {self.data.get('name', '')} partner {partner} found using email address: `{partner.email}`."
            f" The auto-generated website UUID `{message_value.get('uuid')}` for this partner will be"
            f" disregarded. Odoo record: {partner}"
        )

        return partner
