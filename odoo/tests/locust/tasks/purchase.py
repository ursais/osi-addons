# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import helper
from locust import task


class PurchaseTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(PurchaseTaskSet, self).on_start(*args, **kwargs)
        self.Purchase = self.client.env["purchase.order"]

    @task(20)
    def create_new_rfq(self):
        supplier_id = helper.find_random_supplier(self.client)
        product_id = helper.find_random_product_purchase(self.client)
        vals = {
            "partner_id": supplier_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "date_planned": "2020-01-01 00:00:00",
                        "name": product_id.name,
                        "product_id": product_id.id,
                        "product_qty": 1,
                        "product_uom": product_id.uom_id.id,
                        "price_unit": product_id.price and product_id.price or 100.0,
                    },
                )
            ],
        }
        logging.INFO("Created PO with supplier: " + supplier_id.name)
        return self.Purchase.create(vals)

    @task(15)
    def confirm_rfq(self):
        order_id = helper.find_random_rfq(self.client)
        if not order_id:
            logging.INFO("Failed to confirm RFQ -- none found")
            return ()
        return order_id.button_confirm()

    @task(10)
    def receive_products(self):
        picking_id = helper.find_random_picking_in(self.client)
        if not picking_id:
            logging.INFO("Failed to receive DO -- none found")
            return ()
        for product in picking_id.pack_operation_product_ids:
            qty_to_do = product.product_qty
            product.write({"qty_done": qty_to_do})
        return picking_id.do_new_transfer()
