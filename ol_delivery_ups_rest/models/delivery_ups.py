# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import pdf

from .ups_request import OnLogicUPSRequest
from odoo.addons.ol_delivery.models.delivery_request_objects import (
    OnLogicDeliveryPackage,
)


class ProviderUPS(models.Model):
    _inherit = "delivery.carrier"

    ### COLUMNS #######
    negotiated_rates = fields.Boolean("Enable Negotiated Rates", default=False)
    ### END COLUMNS ###

    def ups_rest_rate_shipment(self, order):
        product_data = order.get_product_data_from_sale_order()
        return self.ol_ups_rest_rate_shipment(order, product_data)

    def get_ups_dimensional_weight(self, package_type):
        """
        How do I determine the dimensional weight of my parcel?

        EU:
        https://www.ups.com/nl/en/support/shipping-support/shipping-dimensions-weight#:~:text=How%20do%20I%20determine%20the%20billable%20weight%20of%20my%20parcel,used%20to%20calculate%20the%20rate.
        Dimensional weight reflects parcel density, which is the amount of space a parcel occupies compared to its actual weight.
        Dimensional weight may apply to all UPS domestic and international parcel services.
        Determine the parcel measurement in centimetres. For each measurement, start at the longest point, rounding each measurement to the nearest whole number.
        Multiply the parcel length (longest side of the parcel) by the width by the height. The result is the cubic size in centimeters.
        Divide the cubic size in centimetres by 5,000. Increase any fraction to the next half kilogram.
        Compare the parcel's actual weight to its dimensional weight. The greater of the two is the billable weight and should be used to calculate the rate

        US:
        https://www.ups.com/us/en/support/shipping-support/shipping-dimensions-weight#:~:text=How%20do%20I%20determine%20the%20billable%20weight%20of%20my%20parcel,used%20to%20calculate%20the%20rate
        Determine the package measurement in inches. For each measurement, start at the longest point, rounding each measurement to the nearest whole number.
        Multiply the package length (longest side of the package) by the width by the height. The result is the cubic size in inches.
        Divide the cubic size in inches by the divisor to calculate the dimensional weight in pounds. Increase any fraction to the next whole pound.
        The divisor varies by rate type: 139 for Daily Rates; 166 for Retail Rates. Dimensional Weight = (L x W x H) ÷ Divisor.
        """
        cubic_size = (
            package_type.packaging_length * package_type.width * package_type.height
        )
        if self.env.company.short_name == "us":
            divisor = 166
        elif self.env.company.short_name == "eu":
            divisor = 5000

        return cubic_size / divisor

    def ol_get_packages_from_order(self, order, product_data):
        """

        This is a full override of the `_get_packages_from_order` method from core Odoo
        We do this to support using the product_data instead of the Sale Order directly
        """

        # We use the product_data to get the `total cost` and `total_weight`
        total_cost = product_data.get("total_cost")
        product_total_weight = product_data.get("total_weight")
        product_total_volume = product_data.get("total_volume")
        package_type = self.get_package_type(
            weight=product_total_weight,
            volume=product_total_volume,
            default_package_type=self.ups_default_packaging_id,
        )

        # UPS will use the Billing weight which is the greater of the actual weight and the dimensional weight to determine the shipping cost
        dimensional_weight = self.get_ups_dimensional_weight(package_type)
        total_weight = product_total_weight + package_type.base_weight

        # The rest of the code matches core Odoo's `_get_packages_from_order`
        packages = []
        order_weight = self.env.context.get("order_weight", False)
        total_weight = order_weight or total_weight
        if total_weight == 0.0:
            weight_uom_name = self.env[
                "product.template"
            ]._get_weight_uom_name_from_ir_config_parameter()
            raise UserError(
                _(
                    "The package cannot be created because the total weight of the products in the picking is 0.0 %s",
                    weight_uom_name,
                )
            )

        # If max weight == 0 => division by 0. If this happens, we want to have
        # more in the max weight than in the total weight, so that it only
        # creates ONE package with everything.
        max_weight = package_type.max_weight or total_weight + 1
        total_full_packages = int(total_weight / max_weight)
        last_package_weight = total_weight % max_weight

        package_weights = [max_weight] * total_full_packages + (
            [last_package_weight] if last_package_weight else []
        )
        partial_cost = total_cost / len(package_weights)  # separate the cost uniformly
        order_commodities = self._get_commodities_from_order(order)

        # Split the commodities value uniformly as well
        for commodity in order_commodities:
            commodity.monetary_value /= len(package_weights)
            commodity.qty = max(1, commodity.qty // len(package_weights))

        for weight in package_weights:
            delivery_package = OnLogicDeliveryPackage(
                order_commodities,
                round(weight, 2),
                package_type,
                total_cost=partial_cost,
                currency=order.company_id.currency_id,
                order=order,
            )
            delivery_package.apply_uplift(self.company_id or self.env.company)
            packages.append(delivery_package)
        return packages

    def ol_ups_rest_rate_shipment(self, order, product_data):
        """
        OnLogic's full override of the rate shipment method for UPS
        """

        ups = OnLogicUPSRequest(self)
        packages = self.ol_get_packages_from_order(order, product_data)

        if self.ups_cod:
            cod_info = {
                "currency": order.partner_id.country_id.currency_id.name,
                "monetary_value": order.amount_total,
                "funds_code": self.ups_cod_funds_code,
            }
        else:
            cod_info = None

        check_value = ups._check_required_value(order=order)
        if check_value:
            return {
                "success": False,
                "price": 0.0,
                "error_message": check_value,
                "warning_message": False,
            }

        total_qty = sum(
            [
                line.product_uom_qty
                for line in order.order_line.filtered(
                    lambda line: not line.is_delivery and not line.display_type
                )
            ]
        )

        get_all_services = self.env.context.get("get_all_ups_services", False)
        shipping_buffer = self.env.context.get("shipping_buffer", False)

        results = ups._get_shipping_price(
            shipper=order.company_id.partner_id,
            ship_from=order.warehouse_id.partner_id,
            ship_to=order.partner_shipping_id,
            total_qty=total_qty,
            packages=packages,
            carrier=self,
            order=order,
            cod_info=cod_info,
            get_all_services=get_all_services,
            shipping_buffer=shipping_buffer,
        )

        if isinstance(results, dict) and results.get("error_message"):
            return {
                "success": False,
                "price": 0.0,
                "error_message": _("Error:\n%s", results["error_message"]),
                "warning_message": False,
            }

        service_types = self._get_ups_service_types()

        for result in results:
            if order.currency_id.name == result["currency_code"]:
                price = float(result["price"])
            else:
                quote_currency = self.env["res.currency"].search(
                    [("name", "=", result["currency_code"])], limit=1
                )
                price = quote_currency._convert(
                    float(result["price"]),
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )

            if self.ups_bill_my_account and order.partner_ups_carrier_account:
                # Don't show delivery amount, if ups bill my account option is true
                price = 0.0

            service_name = next(
                (
                    x[1]
                    for x in service_types
                    if x[0] == result.get("service_code", False)
                ),
                None,
            )

            result.update(
                {
                    "success": True,
                    "price": price,
                    "error_message": False,
                    "warning_message": result.get("alert_message", False),
                    "service_name": service_name or "",
                }
            )

        # If we only queried for a specific service we will only have one result
        return results if get_all_services else results[0]

    def ups_rest_send_shipping(self, pickings):
        res = []
        ups = OnLogicUPSRequest(self)
        for picking in pickings:
            packages, shipment_info, ups_service_type, ups_carrier_account, cod_info = (
                self._prepare_shipping_data(picking)
            )

            check_value = ups._check_required_value(picking=picking)
            if check_value:
                raise UserError(check_value)

            result = ups._send_shipping(
                shipment_info=shipment_info,
                packages=packages,
                carrier=self,
                shipper=picking.company_id.partner_id,
                ship_from=picking.picking_type_id.warehouse_id.partner_id,
                ship_to=picking.partner_id,
                service_type=ups_service_type,
                duty_payment=picking.carrier_id.ups_duty_payment,
                saturday_delivery=picking.carrier_id.ups_saturday_delivery,
                cod_info=cod_info,
                label_file_type=self.ups_label_file_type,
                ups_carrier_account=ups_carrier_account,
                picking=picking,
                env=self.env,
            )

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            currency_order = picking.sale_id.currency_id
            if not currency_order:
                currency_order = picking.company_id.currency_id

            if currency_order.name == result["currency_code"]:
                price = float(result["price"])
            else:
                quote_currency = self.env["res.currency"].search(
                    [("name", "=", result["currency_code"])], limit=1
                )
                price = quote_currency._convert(
                    float(result["price"]),
                    currency_order,
                    company,
                    order.date_order or fields.Date.today(),
                )

            package_labels = result.get("label_binary_data", [])

            carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
            logmessage = _(
                "Shipment created into UPS<br/>"
                "<b>Tracking Numbers:</b> %s<br/>"
                "<b>Packages:</b> %s"
            ) % (carrier_tracking_ref, ",".join([p.name for p in packages if p.name]))
            if self.ups_label_file_type != "GIF":
                attachments = [
                    ("LabelUPS-%s.%s" % (pl[0], self.ups_label_file_type), pl[1])
                    for pl in package_labels
                ]
            else:
                attachments = [
                    ("LabelUPS.pdf", pdf.merge_pdf([pl[1] for pl in package_labels]))
                ]
            if result.get("invoice_binary_data"):
                attachments.append(
                    ("UPSCommercialInvoice.pdf", result["invoice_binary_data"])
                )
            picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {
                "exact_price": price,
                "tracking_number": carrier_tracking_ref,
            }
            res = res + [shipping_data]
            if self.return_label_on_delivery:
                try:
                    self.ups_rest_get_return_label(picking)
                except (UserError, ValidationError) as err:
                    try:
                        ups._cancel_shipping(result["tracking_ref"])
                    except ValidationError:
                        pass
                    raise UserError(err)
        return res
