from odoo import http
from odoo.http import Controller, request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(
        "/buy_instance",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def portal_create_user(self, **kw):
        product_id = request.env["product.product"].search(
            [("recurring_invoice", "=", True), ("is_subscription", "=", True)], limit=1
        )
        if not product_id:
            product_id = request.env["product.product"].search(
                [("recurring_invoice", "=", True)], limit=1
            )
        sale_order = request.website.sale_get_order(force_create=True)
        prodcut_exits = sale_order.search(
            [("order_line.product_id", "=", product_id.id), ("id", "=", sale_order.id)]
        )
        if not prodcut_exits:
            sale_order._cart_update(
                product_id=int(product_id.id),
                add_qty=1,
                set_qty=1,
                instance_name=kw["instance_name"],
            )
        return request.redirect("/shop/cart")


class InstancePortal(Controller):
    @http.route("/website_sale/instance_name", type="json", auth="public")
    def portal_get_search(self, data):
        rec = request.env["sale.subscription.line"].sudo().custom_search(data)
        return rec
