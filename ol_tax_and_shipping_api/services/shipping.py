# Import Python Libs
import uuid
import logging
from graphql import GraphQLError
from datetime import datetime

# Import Odoo Libs
from odoo.addons.ol_base.models.tools import get_closest_next_workday_by_delta
from odoo.addons.ol_delivery.models.tools import get_product_data_from_order_lines_data
from odoo import models, _

_logger = logging.getLogger(__name__)


class TSShippingService(models.AbstractModel):
    _name = "ts.shipping.service"
    _inherit = ["ts.base.service"]
    _description = "TS API | Shipping Service"

    def get_data(self, request_data):
        """
        Get the response data for the GQL Shipping query

        Currently only supports UPS Delivery
        """
        print(f"")
        print(f"SHIPPING STARTED")
        mst = datetime.now()
        transaction_id = uuid.uuid4()

        _logger.info(
            f"TS API | SHIPPING | S:1 | Request received | Request: {request_data} | TI: {transaction_id}"
        )
        try:
            st = datetime.now()
            # Get the Odoo company this request is for
            company = self.get_company(request_data)
            print(f"get_company {datetime.now() - st}")
            
            # Check if this request for Shipping is an estimate or not
            is_estimate = request_data.get("is_estimate", False)

            # Switch to the correct company user
            # Make sure we get all UPS services
            # If this request is for an estimate we don't need to validate all the address fields
            self = self.with_user(company.company_user_id).with_context(
                get_all_ups_services=True, no_required_fields=is_estimate
            )

            # Check if this request for Shipping is an estimate or not
            is_estimate = request_data.get("is_estimate", False)

            # Set the carrier
            st = datetime.now()
            ups_delivery_carrier = self.get_ups_delivery_carrier(company)
            print(f"get_ups_delivery_carrier {datetime.now() - st}")
            
            st = datetime.now()
            product_data = get_product_data_from_order_lines_data(env=self.env, company=self.env.company, order_lines_data=request_data.get("lines", []))
            print(f"get_product_data {datetime.now() - st}")

            st = datetime.now()
            sale_order = self.get_sale_order(data=request_data, company=company, add_deliver_line=False)
            print(f"get_sale_order {datetime.now() - st}")

            # Get UPS results
            st = datetime.now()
            ups_results = self.get_ups_delivery_methods(sale_order, product_data, ups_delivery_carrier)
            print(f"get_ups_delivery_methods {datetime.now() - st}")
            
            st = datetime.now()
            additional_results = self.get_additional_delivery_methods(sale_order, product_data)
            print(f"get_additional_delivery_methods {datetime.now() - st}")
            
            results = ups_results + additional_results
        except Exception as error:
            _logger.exception(f"TS API Error | SHIPPING | S:2 | Error: {error} | TI: {transaction_id}")
            raise error
        else:
            _logger.info(
                f"TS API | SHIPPING | S:2 | Processed in {datetime.now() - st} | Result: {results} | TI: {transaction_id}"
            )

        # GraphQL Expects an iterable as the result
        print(f"SHIPPING DONE IN: {datetime.now() - mst}")
        return [results]

    def get_shipping_buffer(self, product_data, delivery_carrier):
        product_buffer = product_data.get("total_shipping_buffer", 0)
        # Get the shipping buffer for the target carrier
        carrier_buffer = delivery_carrier.shipping_buffer
        # The shipping buffer is the sum of the carrier buffer and the largest buffer on any product in the order
        combined_buffer = (product_buffer or 0) + (carrier_buffer or 0)
        
        # Get the nearest workday if the shipping buffer falls on a weekend or holiday
        buffered_date = get_closest_next_workday_by_delta(datetime.now(), combined_buffer)
        return buffered_date
        
    def get_ups_delivery_methods(self, sale_order, product_data, delivery_carrier):
        """
        Get the UPS results.
        """
        
        # Get shipping buffer for products and carriers
        st = datetime.now()
        shipping_buffer = self.get_shipping_buffer(product_data, delivery_carrier)
        # The UPS api requires the date in a specific format
        shipping_buffer = shipping_buffer.strftime("%Y%m%d")
        delivery_carrier = delivery_carrier.with_context(shipping_buffer=shipping_buffer)
        # Get UPS API response for all UPS services it deems being available based on the delivery address
        st = datetime.now()
        ups_results = delivery_carrier.ol_ups_rest_rate_shipment(sale_order, product_data)
        print(f"    ups_rest_rate_shipment {datetime.now() - st}")
        if isinstance(ups_results, dict) and ups_results.get("error_message"):
            raise GraphQLError(f"Err 010: TS API API: UPS API Error: {ups_results.get('error_message')}")

        # Find Odoo's UPS deliver methods that are available for the given company
        st = datetime.now()
        ups_carriers = self.get_odoo_ups_carriers(sale_order)
        print(f"    get_odoo_ups_carriers {datetime.now() - st}")

        results = []
    
        for result in ups_results:
            # Match the UPS response code to Odoo's code.
            ups_carrier = [
                dc
                for dc in ups_carriers
                if dc["message_code"] == result.get("service_code", False)
                and not result.get("is_saturday_delivery", False)
            ]

            if not ups_carrier:
                # If this carrier is not available in Odoo skip it
                continue

            # Set the UUID so we can use it in the response
            result.update(
                {
                    "uuid": ups_carrier[0]["uuid"],
                    "locale": self.env.context.get("lang"),
                    "service_name": _(result.get("service_name", "")),
                }
            )
            results.append(result)
        return results

    def get_odoo_ups_carriers(self, sale_order):
        """
        Find Odoo's UPS deliver methods that are available for the given company
        """
        query = """
        SELECT
            dc.id
        FROM
            delivery_carrier dc
        JOIN product_product pp ON
            pp.id = dc.product_id
        WHERE
            dc.ts_api_enabled = TRUE
            AND (dc.company_id IS NULL 
                OR dc.company_id = %(company_id)s)
            AND dc.active = TRUE
            AND delivery_type = 'ups_rest'
        """
        query_args = {"company_id": sale_order.company_id.id}
        self.env.cr.execute(query, query_args)
        ups_carrier_ids = [x[0] for x in self.env.cr.fetchall()]
        ups_carriers = self.env["delivery.carrier"].browse(ups_carrier_ids)
        return ups_carriers.ts_api_available_carriers(sale_order)

    def get_ups_delivery_carrier(self, company):
        """
        We can choose any carrier as at the end we want to get rates for all of them
        but the current functions need one specific carrier to trigger code from
        """
        
        if company.short_name == "eu":
            # UPS Standard
            res = self.env["delivery.carrier"].search(
                [("delivery_type", "=", "ups_rest"), ("ups_default_service_type", "=", "11")]
            )
            return res

        # UPS Ground
        res = self.env["delivery.carrier"].search(
            [("delivery_type", "=", "ups_rest"), ("ups_default_service_type", "=", "03")]
        )
        return res

    def get_additional_delivery_methods(self, sale_order, product_data):
        """
        Check if `Warehouse Pickup` and `Free Delivery` available
        and return the results for those
        """

        # Find and non UPS delivery carrier that is enabled
        # We exclude UPS as that is handled separately
        query = """SELECT
                    dc.id
                FROM
                    delivery_carrier dc
                JOIN product_product pp ON
                    pp.id = dc.product_id
                WHERE
                    dc.ts_api_enabled = TRUE
                    AND (dc.company_id IS NULL OR dc.company_id = %(company_id)s)
                    AND dc.active = True
                    AND delivery_type NOT IN ('ups_rest', 'ups')
                GROUP BY
                    pp.product_tmpl_id,
                    dc.id
                """
        query_args = {"company_id": sale_order.company_id.id}
        self.env.cr.execute(query, query_args)
        carrier_ids = [x[0] for x in self.env.cr.fetchall()]
        enabled_non_ups_carriers = self.env["delivery.carrier"].browse(carrier_ids)
        # Get Warehouse Pickup and Free Shipping if available
        
        available_carriers = enabled_non_ups_carriers.ts_api_available_carriers(sale_order)

        results = []
        for carrier in available_carriers:
            if carrier.company_id and carrier.company_id != sale_order.company_id:
                # If the Carrier has a company it should match the sale order company
                continue
            # Get shipping buffer for products and carriers
            shipping_buffer = self.get_shipping_buffer(product_data, carrier)
            result = carrier.rate_shipment(sale_order)
            result.update(
                {
                    "service_code": carrier.message_code,
                    "currency_code": sale_order.company_id.currency_id.name,
                    "delivery_time": shipping_buffer or False,
                    "service_name": _(carrier.name),
                    "uuid": carrier.uuid,
                    "locale": self.env.context.get("lang"),
                }
            )
            results.append(result)
        return results
