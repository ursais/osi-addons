# Import Odoo libs
from odoo import _, fields, models
from odoo.exceptions import ValidationError

# Import third-party libs
import minfraud


# Helper methods outside of classes for sending request to MaxMind for fraud score
def _build_request_dict(order):
    """
    Helper function to build the request dictionary needed to send to MaxMind based on the order
    provided.

    Returns a dictionary.
    """
    # build device request settings
    device_dict = {
        "ip_address": order.customer_ip,
        "accept_language": order.accept_language or "",
        "user_agent": order.user_agent or "",
    }
    device_dict = _remove_blank_keys(device_dict)

    # build billing request settings
    billing = order.partner_invoice_id
    billing_dict = {
        "first_name": billing.firstname or "",
        "last_name": billing.lastname or "",
        "company": billing.company_name or "",
        "address": billing.street or "",
        "address_2": billing.street2 or "",
        "postal": billing.zip,
        "city": billing.city,
        "region": billing.state_id.code or "",
        "country": billing.country_id.code or "",
    }
    billing_dict = _remove_blank_keys(billing_dict)

    # build shipping request settings
    shipping = order.partner_shipping_id
    shipping_dict = {
        "first_name": shipping.firstname or "",
        "last_name": shipping.lastname or "",
        "company": shipping.company_name or "",
        "address": shipping.street or "",
        "address_2": shipping.street2 or "",
        "postal": shipping.zip,
        "city": shipping.city,
        "region": shipping.state_id.code or "",
        "country": shipping.country_id.code or "",
    }
    shipping_dict = _remove_blank_keys(shipping_dict)

    request = {
        "device": device_dict,
        "billing": billing_dict,
        "shipping": shipping_dict,
        "order": {"currency": order.currency_id.name, "amount": order.amount_total},
    }

    return request


def _remove_blank_keys(dirty_dict):
    """
    Helper function that removes key/value pairs from the given dictionary if the value is blank.
    Maxmind does not like keys that contain blank values.

    Returns a new dictionary with the key & blank value pairs removed.
    """
    clean_dict = {key: val for key, val in dirty_dict.items() if val != ""}
    return clean_dict


class SaleOrder(models.Model):
    """Inherit sale orders to add fraud check fields and methods."""

    _inherit = "sale.order"

    # COLUMNS #####

    customer_ip = fields.Char("IP Address", readonly=True, copy=False)
    user_agent = fields.Char("User Agent", readonly=True, copy=False)
    accept_language = fields.Char("Accept Language", readonly=True, copy=False)
    check_risk = fields.Boolean("Calculate Risk Score", readonly=True, copy=False)
    maxmind_risk_score = fields.Float("Risk Score", readonly=True, copy=False)
    maxmind_insights = fields.Text("Risk Factors", copy=False)
    sale_payment_method_id = fields.Many2one(
        comodel_name="payment.method",
        string="Payment Method",
    )

    # END ########
    # MEHTODS ####

    def action_confirm(self):
        """
        Check to make sure sale_payment_method_id is set as it's required for confirmation.
        Calculate risk scores for any Sale Order that requires a score but is missing one.
        """

        # First check for original request date and raise validation error if not set
        for rec in self:
            if not rec.sale_payment_method_id:
                raise ValidationError(
                    _("Payment Method is required to confirm the order.")
                )

        # Get and set the risk score for the order
        self._get_risk_score()
        return super().action_confirm()

    def _get_risk_score(self):
        """
        Compute risk score for an order
        """
        IrConfigSudo = self.env["ir.config_parameter"].sudo()
        config_client = IrConfigSudo.get_param("ol_fraud_detection.maxmind_client_id")
        config_key = IrConfigSudo.get_param("ol_fraud_detection.maxmind_key")
        client = minfraud.Client(int(config_client), config_key)

        for order in self:
            # Check risk if payment method is configured and we have an IP
            if (
                order.customer_ip
                and order.sale_payment_method_id
                and order.sale_payment_method_id.check_risk
            ):
                order.check_risk = True

            if order.check_risk and not order.maxmind_risk_score:
                if not order.customer_ip:
                    # Missing IP makes check impossible
                    order.maxmind_risk_score = 99
                    order.maxmind_insights = order._get_formatted_insights(None)
                    continue

                request = _build_request_dict(order)
                try:
                    # Get risk, insights from MaxMind
                    score = client.score(request)
                    insights = client.insights(request)
                except minfraud.MinFraudError as err:
                    # Private IPs, badly formatted data can cause errors,
                    # set risk score high to be safe and trigger a hold, but
                    # don't break payment processing for the customer.
                    order.maxmind_risk_score = 99
                    msg = f"Could Not Calculate Score: {err}"
                    order.maxmind_insights = msg
                    continue
                order.maxmind_insights = order._get_formatted_insights(insights)
                order.maxmind_risk_score = score.risk_score

    def _get_formatted_insights(self, insights):
        """
        Based on the available attributes, build a message from MaxMind insights object
        """

        self.ensure_one()
        # Short circuit if no IP address was available. This shouldn't happen
        if not self.customer_ip or not insights:
            return "IP address not found, maxmind score not available."

        txt = ""
        ip_country = False
        billing_country = self.partner_invoice_id.country_id.name
        ip_res = insights.ip_address

        # Special explanation
        if hasattr(insights, "explanation"):
            txt += f"{insights.explanation}\n"

        # Get IP country (in english)
        if hasattr(ip_res, "registered_country"):
            ip_country = (
                ip_res.registered_country.names["en"]
                if ip_res.registered_country.names
                else False
            )

        # IP Address results
        if hasattr(ip_res, "traits"):
            if ip_res.traits.isp:
                txt += f"Customer's ISP is {ip_res.traits.isp}.\n"
            if ip_res.traits.is_anonymous_proxy:
                txt += "Anonymous proxy was used.\n"
            if ip_res.traits.is_anonymous_vpn:
                txt += "Anonymous VPN was used.\n"
            if ip_res.traits.is_public_proxy:
                txt += "Public proxy was used.\n"
            if ip_res.traits.is_tor_exit_node:
                txt += "Tor exit node was used.\n"

        # Billing Address results
        if hasattr(insights, "billing_address"):
            billing = insights.billing_address
            distance = billing.distance_to_ip_location
            if not distance:
                txt += f"Could'nt calculate Estimated distance between billing location and IP address"
            elif distance > 0:
                txt += (
                    f"Estimated distance between billing location and IP address is "
                    f"{distance} km.\n"
                )
            if not billing.is_in_ip_country:
                txt += f"Customer stated billing country as {billing_country} but IP address "
                if ip_country:
                    txt += f"is located in {ip_country}.\n"
                else:
                    txt += f"country couldn't be identified.\n"
            if billing.is_postal_in_city is False:
                txt += "Billing postcode does not match city.\n"

        # Email address results
        if hasattr(insights, "email"):
            if insights.email.is_free:
                txt += "Free email address was used.\n"
            if insights.email.is_high_risk:
                txt += "Email was found in high risk database.\n"

        if hasattr(insights, "shipping_address"):
            shipping = insights.shipping_address
            if shipping.is_high_risk:
                txt += "Shipping address is a known mail forwarding service.\n"
            if shipping.is_postal_in_city is False:
                txt += "Shipping postcode does not match city.\n"

        if hasattr(insights, "warnings") and insights.warnings:
            txt += "Warnings:\n"
            for service_warning in insights.warnings:
                txt += f"{service_warning.warning}\n"

        return txt

    # END ########
