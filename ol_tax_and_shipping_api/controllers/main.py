# Import Python libs
import logging
from odoo.http import request

# Import Odoo libs
from odoo import http
from odoo.tools.profiler import Profiler

_logger = logging.getLogger(__name__)


class TaxAndShippingController(http.Controller):

    @http.route('/onlogic-api/shipping', type='json', auth='ts_api', methods=['POST'], csrf=False)
    def ts_shipping(self, **kwargs):

        # Add a new context variable so we know the authentication was successful
        request.update_context(tax_and_shipping_api_client_signature_validated = True)
        try:
            request_data = request.get_json_data()
            with Profiler():
                # TODO: !!! REMOVE THIS PROFILER !!!
                results = http.request.env['ts.shipping.service'].sudo().get_data(request_data=request_data)
            return results
        except Exception as error:
            _logger.exception(f"TS API | SHIPPING | Error: {error}")
            return {"error": str(error)}
    
    @http.route('/onlogic-api/tax', type='json', auth='ts_api', methods=['POST'], csrf=False)
    def ts_tax(self, **kwargs):
        # Add a new context variable so we know the authentication was successful
        request.update_context(tax_and_shipping_api_client_signature_validated = True)
        try:
            request_data = request.get_json_data()
            with Profiler():
                # TODO: !!! REMOVE THIS PROFILER !!!
                results = http.request.env['ts.tax.service'].sudo().get_data(request_data=request_data)
            return results
        except Exception as error:
            _logger.exception(f"TS API | TAX | Error: {error}")
            return {"error": str(error)}
