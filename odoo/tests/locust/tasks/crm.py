# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import random

import helper
from locust import task


class CRMTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(CRMTaskSet, self).on_start(*args, **kwargs)
        self.Lead = self.client.env["crm.lead"]
        self.Sale = self.client.env["sale.order"]
        self.Partner = self.client.env["res.partner"]

    @task(20)
    def create_lead(self):
        partner_rec = helper.find_random_customer(self.client)
        team_rec = helper.search_browse(
            self.client, "crm.team", [("name", "=", "Direct Sales")], random_pick=True
        )
        stage_rec = helper.search_browse(
            self.client,
            "crm.stage",
            [("team_id", "=", False), ("name", "=", "New")],
            random_pick=True,
        )
        vals = {
            "probability": 10,
            "team_id": team_rec.id,
            "partner_id": partner_rec.id,
            "planned_revenue": random.randrange(
                1000, 100001, 1000
            ),  # random revenue from 1k to 10k by 1k increments
            "priority": str(random.randrange(0, 4, 1)),  # random priority from 0-3
            "type": "opportunity",
            "name": partner_rec.name,
            "stage_id": stage_rec.id,
        }
        lead_id = self.Lead.create(vals)
        logging.INFO("Created Lead: " + partner_rec.name)
        return lead_id

    @task(4)
    def mark_lead_won(self):
        lead_rec = helper.find_random_new_lead(self.client)
        if not lead_rec:
            logging.INFO("Failed to mark Lead won -- none found")
            return ()
        return lead_rec.action_set_won()

    @task(4)
    def create_quotation(self):
        lead_rec = helper.find_random_won_lead(self.client)
        if not lead_rec:
            logging.INFO("Failed to create Quotation -- no Lead found")
            return ()
        vals = {
            "partner_id": lead_rec.partner_id.id,
            "state": "draft",
            "opportunity_id": lead_rec.id,
            "partner_invoice_id": lead_rec.partner_id.id,
            "partner_shipping_id": lead_rec.site_id.id,
            "pricelist_id": lead_rec.partner_id.property_product_pricelist.id,
        }
        sale_id = self.Sale.create(vals)
        if type(sale_id) != int:
            sale_id = sale_id.id
        sale_rec = self.Sale.browse(sale_id)
        # separate order creation and lines, onchange will clear lines
        product_ids = []
        for x in range(0, 3):
            domain = [("id", "not in", product_ids)] if x > 0 else []
            prod = helper.find_associated_product(
                self.client, sale_rec.partner_shipping_id, domain
            )
            product_ids += [prod.id]
        product_ids = self.client.env["product.product"].browse(product_ids)
        sale_order_line = self.client.env["sale.order.line"]
        for p in product_ids:
            vals = {
                "name": p.name,
                "product_id": p.id,
                "product_uom_qty": 1,
                "product_uom": p.uom_id.id,
                "price_unit": p.list_price,
                "order_id": sale_rec.id,
            }
            sale_order_line.create(vals)
        logging.INFO("Created SO: " + sale_rec.name)
        return sale_rec

    @task(3)
    def confirm_quotation(self):
        quote_id = helper.find_random_quotation(self.client)
        if not quote_id:
            logging.INFO("Failed to confirm Quotation -- none found")
            return ()
        return quote_id.action_confirm()
