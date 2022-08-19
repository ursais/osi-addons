# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import random
from datetime import datetime

import helper
from locust import task


class SaleTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(SaleTaskSet, self).on_start(*args, **kwargs)
        self.Sale = self.client.env["sale.order"]
        self.now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    @task(10)
    def create_sale_order(self):
        """Create and confirm a sales order with one line"""
        vals = {
            "partner_id": 17591,
            "picking_policy": "direct",
            "date_order": self.now,
            "user_id": 1,
            "contract_type_id": 1,
            "pricelist_id": 1,
            "validity_date": "2020-08-31",
            "warehouse_id": 1,
            "partner_invoice_id": 17591,
            "partner_shipping_id": 193636,
            "template_id": 3,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": 21052,
                        "price_unit": 1000,
                        "product_uom_qty": 1,
                        "price_subtotal": 1000,
                        "currency_id": 1,
                        "product_uom": 1,
                        "purchase_price": 200,
                        "price_total": 1000,
                        "name": "Main Product",
                        "salesman_id": 1,
                    },
                )
            ],
        }
        sale_id = self.Sale.create(vals)
        self.Sale.browse(sale_id).action_confirm()

    @task(10)
    def create_big_sale_order(self):
        """Create and confirm a sales order with more than 10 lines"""
        vals = {
            "partner_id": 17591,
            "picking_policy": "direct",
            "date_order": self.now,
            "user_id": 1,
            "contract_type_id": 1,
            "pricelist_id": 1,
            "validity_date": "2020-08-31",
            "warehouse_id": 1,
            "partner_invoice_id": 17591,
            "partner_shipping_id": 193636,
            "template_id": 3,
            "order_line": [],
        }
        lines = []
        random_number = random.randint(10, 50)
        for _i in range(3, random_number):
            product = helper.find_random_product_sale(self.client)
            line = (
                0,
                0,
                {
                    "price_unit": product.lst_price,
                    "product_uom_qty": 1,
                    "price_subtotal": product.lst_price * 1,
                    "currency_id": 1,
                    "product_uom": product.uom_id.id,
                    "can_edit": True,
                    "price_total": product.lst_price * 1,
                    "name": product.display_name,
                    "product_id": product.id,
                },
            )
            lines.append(line)
        vals.update({"order_line": lines})
        sale_id = self.Sale.create(vals)
        self.Sale.browse(sale_id).action_confirm()
