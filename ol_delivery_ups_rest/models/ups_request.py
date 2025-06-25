import logging
import pprint
import datetime as dt
from json.decoder import JSONDecodeError

_logger = logging.getLogger(__name__)


from odoo import _
from odoo.addons.ol_base.models.tools import option_to_val
from odoo.addons.delivery_ups_rest.models import ups_request
from odoo.exceptions import ValidationError

# We override the UPS API URLs and API version
ups_request.TEST_BASE_URL = "https://wwwcie.ups.com"
ups_request.PROD_BASE_URL = "https://onlinetools.ups.com"
ups_request.API_VERSION = "v2409"
ups_request.TOKEN_TYPE = "Bearer"


class OnLogicUPSRequest(ups_request.UPSRequest):

    def format_float(self, number):
        """
        Formats a float to 6 digits with 2 decimal places and returns it as a string.
        """
        return str(round(number, 2))

    def _get_shipping_price(
        self,
        shipper,
        ship_from,
        ship_to,
        total_qty,
        packages,
        carrier,
        order,
        cod_info=None,
        get_all_services=False,
        shipping_buffer=False,
    ):
        service_type = carrier.ups_default_service_type
        saturday_delivery = carrier.ups_saturday_delivery
        total_weight = sum(p.weight for p in packages)

        # Set the Request Option based on if we need to return rates for one service or multiple
        request_option = "Shoptimeintransit" if get_all_services else "Rate"
        url = f"/api/rating/{ups_request.API_VERSION}/{request_option}"

        shipment = {
            "Package": self._set_package_details(packages, carrier, ship_from, ship_to, cod_info),
            "Shipper": self._get_ship_data_from_partner(shipper, self.shipper_number),
            "ShipFrom": self._get_ship_data_from_partner(ship_from),
            "ShipTo": self._get_ship_data_from_partner(ship_to),
            "NumOfPieces": str(int(total_qty)),
            "ShipmentServiceOptions": (
                {"SaturdayDeliveryIndicator": saturday_delivery} if saturday_delivery else None
            ),
            "ShipmentTotalWeight": {
                "UnitOfMeasurement": {
                    "Code": carrier.ups_package_weight_unit,
                    "Description": option_to_val(
                        carrier, "ups_package_weight_unit", carrier.ups_package_weight_unit
                    ),
                },
                "Weight": self.format_float(total_weight),
            },
            "InvoiceLineTotal": {
                "CurrencyCode": order.partner_id.country_id.currency_id.name,
                "MonetaryValue": self.format_float(
                    sum([line.price_subtotal for line in order.order_line if not line.is_delivery])
                ),
            },
            "DeliveryTimeInformation": {
                "PackageBillType": "03",
                "Pickup": {
                    "Date": shipping_buffer or dt.datetime.now().strftime("%Y%m%d"),
                    "Time": "1600",
                },
            },
        }

        if not get_all_services:
            shipment.update(
                {
                    "Service": {
                        "Code": service_type,
                    }
                }
            )

        if carrier.negotiated_rates:
            shipment.update(
                {
                    "ShipmentRatingOptions": {
                        "NegotiatedRatesIndicator": "Y",
                    }
                }
            )

        data = {
            "RateRequest": {
                "Request": {
                    "RequestOption": request_option,
                },
                "PickupType": {"Code": "01", "Description": "Daily Pickup"},
                "CustomerClassification": {"Code": "01", "Description": "Daily Pickup"},
                "Shipment": shipment,
            },
        }

        res = self._send_request(url, method="POST", json=data)
        order.ups_request_log = pprint.pformat(data, indent=1)
        if not res.ok:
            res = {"error_message": self._process_errors(res.json())}
            order.ups_response_log = pprint.pformat(res, indent=1)
            return res

        res = res.json()
        order.ups_response_log = pprint.pformat(res, indent=1)

        price = 0
        currency_code = None
        currencies = []
        results = []

        for rate in res["RateResponse"]["RatedShipment"]:

            charge = rate["TotalCharges"]

            # Some users are qualified to receive negotiated rates
            if (
                "NegotiatedRateCharges" in rate
                and rate["NegotiatedRateCharges"]["TotalCharge"]["MonetaryValue"]
            ):
                charge = rate["NegotiatedRateCharges"]["TotalCharge"]

            currencies.append(charge["CurrencyCode"])
            currency_code = charge["CurrencyCode"]
            price = float(charge["MonetaryValue"])

            result = {
                "currency_code": currency_code,
                "price": price,
                "alert_message": self._process_alerts(res["RateResponse"]["Response"]),
                "service_code": rate.get("Service", {}).get("Code", None),
            }

            if get_all_services:
                delivery_time_information = self.get_delivery_time_information(rate)
                result.update(delivery_time_information)

            results.append(result)

        if len(set(currencies)) != 1:
            msg = f"UPS REST: Different currencies in UPS response: {currencies}"
            if self.sale_order:
                msg = f"{msg} | Sale Order: {self.sale_order.name} ({self.sale_order.id})"
            _logger.error(msg)
        return results

    def get_delivery_time_information(self, rate):
        """
        Get the delivery time information from the rate response
        """

        service_summary = rate.get("TimeInTransit", {}).get("ServiceSummary", {})
        arrival = service_summary.get("EstimatedArrival", {}).get("Arrival", {})
        arrival_date = arrival.get("Date", False)
        arrival_time = arrival.get("Time", False)
        # TimeInTransit information may not always be available. If it is not, then we should return nothing
        # so the request does not fail
        if arrival_date and arrival_time:
            delivery_time = dt.datetime.strptime(f"{arrival_date} {arrival_time}", "%Y%m%d %H%M%S")
            return {
                "delivery_time": delivery_time or "",
                "is_saturday_delivery": bool(int(service_summary.get("SaturdayDelivery", 0))),
            }
        return {}

    def _check_required_value(self, order=False, picking=False, is_return=False):

        if (order and order.env.context.get("no_required_fields", False)) or (
            picking and picking.env.context.get("no_required_fields", False)
        ):
            # Allow us to skip the required fields check
            return False

        if order:
            shipper = order.company_id.partner_id
            ship_from = order.warehouse_id.partner_id
            ship_to = order.partner_shipping_id
        elif picking and is_return:
            ship_to = picking.picking_type_id.warehouse_id.partner_id
        else:
            shipper = picking.company_id.partner_id
            ship_from = picking.picking_type_id.warehouse_id.partner_id
            ship_to = picking.partner_id
        required_field = {"city": "City", "country_id": "Country", "phone": "Phone"}
        # Check required field for shipper
        res = [required_field[field] for field in required_field if not shipper[field]]
        # OnLogic: We don't want to check state based on the country
        # if shipper.country_id.code in ("US", "CA", "IE") and not shipper.state_id.code:
        #     res.append("State")
        if not shipper.street and not shipper.street2:
            res.append("Street")
        if shipper.country_id.code != "HK" and not shipper.zip:
            res.append("ZIP code")
        if res:
            return _(
                "The address of your company is missing or wrong.\n(Missing field(s) : %s)", ",".join(res)
            )
        # OnLogic: We don't want to check the phone number's length
        # if len(self._clean_phone_number(shipper.phone)) < 10:
        # return _("Shipper Phone must be at least 10 alphanumeric characters.")
        # Check required field for warehouse address
        res = [required_field[field] for field in required_field if not ship_from[field]]
        # OnLogic: We don't want to check state based on the country
        # if ship_from.country_id.code in ("US", "CA", "IE") and not ship_from.state_id.code:
        # res.append("State")
        if not ship_from.street and not ship_from.street2:
            res.append("Street")
        if ship_from.country_id.code != "HK" and not ship_from.zip:
            res.append("ZIP code")
        if res:
            return _(
                "The address of your warehouse is missing or wrong.\n(Missing field(s) : %s)", ",".join(res)
            )
        # OnLogic: We don't want to check the phone number's length
        # if len(self._clean_phone_number(ship_from.phone)) < 10:
        # return (_("Warehouse Phone must be at least 10 alphanumeric characters."),)
        # Check required field for recipient address
        res = [required_field[field] for field in required_field if field != "phone" and not ship_to[field]]
        # OnLogic: We don't want to check state based on the country
        # if ship_to.country_id.code in ("US", "CA", "IE") and not ship_to.state_id.code:
        # res.append("State")
        if not ship_to.street and not ship_to.street2:
            res.append("Street")
        if ship_to.country_id.code != "HK" and not ship_to.zip:
            res.append("ZIP code")
        # OnLogic: We don't want to check address street length
        # if len(ship_to.street or "") > 35 or len(ship_to.street2 or "") > 35:
        #     return _(
        #         "UPS address lines can only contain a maximum of 35 characters. You can split the contacts addresses on multiple lines to try to avoid this limitation."
        #     )
        if picking and not order:
            order = picking.sale_id
        phone = ship_to.mobile or ship_to.phone
        if order and not phone:
            phone = order.partner_id.mobile or order.partner_id.phone
        if order:
            if not order.order_line:
                return _("Please provide at least one item to ship.")
            for line in order.order_line.filtered(
                lambda line: not line.product_id.weight
                and not line.is_delivery
                and line.product_id.type not in ["service", "digital", False]
            ):
                return _(
                    "The estimated price cannot be computed because the weight of your product %s is missing.",
                    line.product_id.display_name,
                )
        if picking:
            for ml in picking.move_line_ids.filtered(
                lambda ml: not ml.result_package_id and not ml.product_id.weight
            ):
                return _(
                    "The delivery cannot be done because the weight of your product %s is missing.",
                    ml.product_id.display_name,
                )
            packages_without_weight = picking.move_line_ids.mapped("result_package_id").filtered(
                lambda p: not p.shipping_weight
            )
            if packages_without_weight:
                return _(
                    "Packages %s do not have a positive shipping weight.",
                    ", ".join(packages_without_weight.mapped("display_name")),
                )
        if not phone:
            res.append("Phone")
        if res:
            return _("The recipient address is missing or wrong.\n(Missing field(s) : %s)", ",".join(res))
        # OnLogic: We don't want to check the phone number's length
        # if len(self._clean_phone_number(phone)) < 10:
        # return (_("Recipient Phone must be at least 10 alphanumeric characters."),)
        return False

    def _send_shipping(
        self,
        shipment_info,
        packages,
        carrier,
        shipper,
        ship_from,
        ship_to,
        service_type,
        duty_payment,
        saturday_delivery=False,
        cod_info=None,
        label_file_type="GIF",
        ups_carrier_account=False,
        is_return=False,
        picking=None,
    ):
        url = f"/api/shipments/{ups_request.API_VERSION}/ship"
        # Payment Info
        shipment_charge = {
            "Type": "01",
        }
        payment_info = [shipment_charge]
        if ups_carrier_account:
            shipment_charge["BillReceiver"] = {
                "AccountNumber": ups_carrier_account,
                "Address": {
                    "PostalCode": ship_to.zip,
                },
            }
        else:
            shipment_charge["BillShipper"] = {
                "AccountNumber": self.shipper_number,
            }
        if duty_payment == "SENDER":
            payment_info.append(
                {
                    "Type": "02",
                    "BillShipper": {"AccountNumber": self.shipper_number},
                }
            )
        shipment_service_options = {}
        if shipment_info.get("require_invoice"):
            shipment_service_options["InternationalForms"] = self._set_invoice(
                shipment_info, [c for pkg in packages for c in pkg.commodities], ship_to, is_return
            )
            shipment_service_options["InternationalForms"]["PurchaseOrderNumber"] = shipment_info.get(
                "purchase_order_number"
            )
            shipment_service_options["InternationalForms"]["TermsOfShipment"] = shipment_info.get(
                "terms_of_shipment"
            )
        if saturday_delivery:
            shipment_service_options["SaturdayDeliveryIndicator"] = saturday_delivery

        request = {
            "ShipmentRequest": {
                "Request": {
                    "RequestOption": "nonvalidate",
                },
                "LabelSpecification": {
                    "LabelImageFormat": {
                        "Code": label_file_type,
                    },
                    "LabelStockSize": {"Height": "6", "Width": "4"} if label_file_type != "GIF" else None,
                },
                "Shipment": {
                    "Description": shipment_info.get("description"),
                    "ReturnService": {"Code": "9"} if is_return else None,
                    "Package": self._set_package_details(
                        packages, carrier, ship_from, ship_to, cod_info, ship=True, is_return=is_return
                    ),
                    "Shipper": self._get_ship_data_from_partner(shipper, self.shipper_number),
                    "ShipFrom": self._get_ship_data_from_partner(ship_from),
                    "ShipTo": self._get_ship_data_from_partner(ship_to),
                    "Service": {
                        "Code": service_type,
                    },
                    "NumOfPiecesInShipment": (
                        int(shipment_info.get("total_qty")) if service_type == "96" else None
                    ),
                    "ShipmentServiceOptions": shipment_service_options if shipment_service_options else None,
                    "ShipmentRatingOptions": {
                        # TODO: This should be dependent on the carrier's negotiated_rates setting
                        "NegotiatedRatesIndicator": "1",
                    },
                    "PaymentInformation": {
                        "ShipmentCharge": payment_info,
                    },
                },
            },
        }

        # Include ReferenceNumber only if the shipment is not US/US or PR/PR
        if not (
            (ship_from.country_id.code == "US" and ship_to.country_id.code == "US")
            or (ship_from.country_id.code == "PR" and ship_to.country_id.code == "PR")
        ):
            request["ShipmentRequest"]["Shipment"]["ReferenceNumber"] = {
                "Value": shipment_info.get("reference_number")
            }

        # Shipments from US to CA or PR require extra info
        if ship_from.country_id.code == "US" and ship_to.country_id.code in ["CA", "PR"]:
            request["ShipmentRequest"]["Shipment"]["InvoiceLineTotal"] = {
                "CurrencyCode": shipment_info.get("itl_currency_code"),
                "MonetaryValue": shipment_info.get("ilt_monetary_value"),
            }
        res = self._send_request(url, "POST", json=request)
        picking.ups_request_log = pprint.pformat(request, indent=1)
        if res.status_code == 401:
            msg = "Invalid Authentication Information: Please check your credentials and configuration within UPS's system."
            picking.ups_response_log = pprint.pformat(res, indent=1)
            raise ValidationError(_(msg))
        try:
            res_body = res.json()
        except JSONDecodeError as err:
            self.logger(str(err), f"ups response decode error {url}")
            raise ValidationError(_("Could not decode response"))
        if not res.ok:
            raise ValidationError(self._process_errors(res.json()))
        picking.ups_response_log = pprint.pformat(res_body, indent=1)
        result = {}
        shipment_result = res_body["ShipmentResponse"]["ShipmentResults"]
        packs = shipment_result.get("PackageResults", [])
        # get package labels
        if not isinstance(packs, list):
            packs = [packs]
        result["tracking_ref"] = shipment_result["ShipmentIdentificationNumber"]
        labels_binary = [
            (
                pack["TrackingNumber"],
                self._save_label(pack["ShippingLabel"]["GraphicImage"], label_file_type=label_file_type),
            )
            for pack in packs
        ]
        result["label_binary_data"] = labels_binary
        # save international form if in response
        international_form = shipment_result.get("Form", False)
        if international_form:
            result["invoice_binary_data"] = self._save_label(
                international_form["Image"]["GraphicImage"], label_file_type="pdf"
            )
        # Some users are qualified to receive negotiated rates
        if shipment_result.get("NegotiatedRateCharges"):
            charge = shipment_result["NegotiatedRateCharges"]["TotalCharge"]
        else:
            charge = shipment_result["ShipmentCharges"]["TotalCharges"]
        result["currency_code"] = charge["CurrencyCode"]
        result["price"] = charge["MonetaryValue"]
        return result
