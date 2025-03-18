# Import Odoo libs
from odoo import http
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal


class OnLogicCustomerPortal(CustomerPortal):
    @http.route(
        "/my/orders/<int:order_id>/transaction/token",
        type="http",
        auth="public",
        website=True,
    )
    def payment_token(self, order_id, pm_id=None, **kwargs):
        """
        Get the information for Fraud Detection
        """
        # Get order and all available headers
        order = request.env["sale.order"].sudo().browse(order_id)
        if not order:
            return super(OnLogicCustomerPortal, self).payment_token(
                order_id=order_id, pm_id=pm_id, **kwargs
            )

        self.add_fraud_detection_information(request, order)

        return super(OnLogicCustomerPortal, self).payment_token(
            order_id=order_id, pm_id=pm_id, **kwargs
        )

    @http.route(
        ["/my/orders/<int:order_id>/transaction/"],
        type="json",
        auth="public",
        website=True,
    )
    def payment_transaction_token(
        self, acquirer_id, order_id, save_token=False, access_token=None, **kwargs
    ):
        """
        Get the information for Fraud Detection.
        """

        # Ensure a payment acquirer is selected
        if not acquirer_id:
            return False

        try:
            # Ensure a payment acquirer exists
            acquirer_id = int(acquirer_id)
        except:
            return False

        order = request.env["sale.order"].sudo().browse(order_id)
        if not order:
            return super(OnLogicCustomerPortal, self).payment_transaction_token(
                acquirer_id, order_id, save_token, access_token, **kwargs
            )

        self.add_fraud_detection_information(request, order)

        return super(OnLogicCustomerPortal, self).payment_transaction_token(
            acquirer_id, order_id, save_token, access_token, **kwargs
        )

    @staticmethod
    def add_fraud_detection_information(request, order):
        """
        Get the different Fraud Detection related information from the request and the SaleOrder
        """

        env = request.httprequest.environ
        env_vars = env.keys()

        # Click to buy used, flag for fraud detection and get variables
        order.check_risk = True
        if "HTTP_USER_AGENT" in env_vars:
            order.user_agent = env["HTTP_USER_AGENT"]
        if "HTTP_ACCEPT_LANGUAGE" in env_vars:
            order.accept_language = env["HTTP_ACCEPT_LANGUAGE"]

        # Prefer x-forwarded-for for webscale environments, fall back to remote_addr
        if "HTTP_X_FORWARDED_FOR" in env_vars:
            header_val = env["HTTP_X_FORWARDED_FOR"]
            # Assume first IP in list is the correct client IP
            first = [x.strip() for x in header_val.split(",")][0]
            order.customer_ip = first
        elif "REMOTE_ADDR" in env_vars:
            order.customer_ip = env["REMOTE_ADDR"]
