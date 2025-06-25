# Import Python Libs
import uuid
import logging
from datetime import datetime

# Import Odoo Libs
from odoo import models

_logger = logging.getLogger(__name__)


class TSTaxService(models.AbstractModel):
    _name = "ts.tax.service"
    _inherit = ["ts.base.service"]
    _description = "TS API | Tax Service"

    def get_data(self, request_data):
        """
        Get the response data for taxes.
        For US we return Avatax calculation
        fro EU we use VAT calculation
        """
        print(f"")
        print(f"TAXES STARTED")
        from datetime import datetime

        mst = datetime.now()
        transaction_id = uuid.uuid4()

        _logger.info(
            f"TS API | TAX | S:1 | Request received | Request: {request_data} | TI: {transaction_id}"
        )

        try:
            request_data = self.validate_request_data(request_data)
            st = datetime.now()
            # Get the Odoo company this request is for
            company = self.get_company(request_data)
            print(f"get_company {datetime.now() - st}")

            # Switch to the correct company user
            self = self.with_user(company.company_user_id)

            # Create a pseudo sale order to be able to run correct calculations
            st = datetime.now()
            sale_order = self.get_sale_order(data=request_data, company=company, add_deliver_line=True)
            print(f"get_sale_order {datetime.now() - st}")

            # Update the Sale Order data before we pull VAT info
            st = datetime.now()
            sale_order.with_context(is_tax_and_shipping_call=True).avalara_compute_taxes()
            print(f"avalara_compute_taxes {datetime.now() - st}")

            st = datetime.now()
            lines = []

            amount_untaxed = 0
            amount_tax = 0
            amount_total = 0
            for line in sale_order.order_line:
                taxes = []
                for tax in line.tax_id:
                    taxes.append({"name": tax.name, "amount_type": tax.amount_type, "amount": tax.amount})

                if line.is_delivery:
                    shipping_method = request_data.get("shipping_method", False)
                    product_uuid = str(sale_order.carrier_id.product_id.uuid)
                    price_unit = shipping_method.get("price")
                else:
                    request_line_data = next(
                        (l for l in request_data.get("lines", []) if l.get("order_line_uuid") == line.uuid),
                        {},
                    )
                    product_uuid = request_line_data.get("product_id")
                    price_unit = request_line_data.get("price_unit")

                lines.append(
                    {
                        "is_delivery": line.is_delivery,
                        "product_id": product_uuid,
                        "price_unit": round(price_unit, 4),
                        "qty": int(line.product_uom_qty),
                        "price_tax": round(line.price_tax, 4),
                        "currency_code": sale_order.company_id.currency_id.name,
                        "taxes": taxes,
                        "order_line_uuid": line.uuid,
                    }
                )
                line_amount_untaxed = price_unit * line.product_uom_qty
                line_amount_tax = line.price_tax
                amount_untaxed += line_amount_untaxed
                amount_tax += line_amount_tax
                amount_total += line_amount_untaxed + line_amount_tax
            results = {
                "totals": {
                    "amount_untaxed": round(amount_untaxed, 4),
                    "amount_tax": round(amount_tax, 4),
                    "amount_total": round(amount_total, 4),
                    "currency_code": sale_order.company_id.currency_id.name,
                },
                "lines": lines,
            }
        except Exception as error:
            _logger.exception(f"TS API Error | TAX | S:2 | Error: {error} | TI: {transaction_id}")
            raise error
        else:
            _logger.info(
                f"TS API | TAX | S:2 | Processed in {datetime.now() - mst} | Result: {results} | TI: {transaction_id}"
            )
        # GraphQL Expects an iterable as the result
        print(f"TAXES DONE IN: {datetime.now() - st}")
        return [results]

    def validate_request_data(self, request_data):
        """
        The goal of this function is to validate the request data
        and to add missing items if necessary.
        """
        for line in request_data.get("lines", []):
            if not line.get("order_line_uuid"):
                line["order_line_uuid"] = str(uuid.uuid4())
        return request_data
