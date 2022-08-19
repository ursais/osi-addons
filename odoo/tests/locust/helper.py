# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import random

from locust import TaskSet


class BaseBackendTaskSet(TaskSet):
    def on_start(self):
        self.client.login(self.user.db_name, self.user.login, self.user.password)


def search_browse(client, model, domain, random_pick=False):
    Model = client.env[model]
    record_ids = Model.search_read(domain, ["id"])
    if len(record_ids) == 0:
        return False
    elif random_pick:
        record_ids = random.choice(record_ids)["id"]
    else:
        record_ids = [rek["id"] for rek in record_ids]
    browse_records = Model.browse(record_ids)
    return browse_records


def find_random_delivery(client):
    model = "stock.picking"
    domain = [("origin", "!=", False), ("state", "=", "confirmed")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_invoice_draft(client):
    model = "account.invoice"
    domain = [("type", "=", "out_invoice"), ("state", "=", "draft")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_invoice_open(client):
    model = "account.invoice"
    domain = [("type", "=", "out_invoice"), ("state", "=", "open")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_new_lead(client):
    model = "crm.lead"
    domain = [("stage_id.name", "=", "New")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_picking_in(client):
    model = "stock.picking"
    domain = [("state", "=", "assigned")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_picking_wave(client):
    model = "stock.picking.wave"
    domain = [("state", "in", ("in_progress", "done"))]
    return search_browse(client, model, domain, random_pick=True)


def find_random_picking_wave_running(client):
    model = "stock.picking.wave"
    domain = [("state", "=", "in_progress")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_product_purchase(client):
    model = "product.product"
    domain = [("purchase_ok", "=", True)]
    return search_browse(client, model, domain, random_pick=True)


def find_random_product_sale(client):
    model = "product.product"
    domain = [("sale_ok", "=", True), ("type", "=", "product")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_purchase_order(client):
    model = "purchase.order"
    domain = [("invoice_status", "=", "to invoice")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_quotation(client):
    model = "sale.order"
    domain = [
        ("state", "=", "draft"),
        ("order_line", "!=", False),
        ("date_order", ">", "2020-07-20"),
    ]
    return search_browse(client, model, domain, random_pick=True)


def find_random_rfq(client):
    model = "purchase.order"
    domain = [("state", "=", "draft")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_sale_order(client):
    model = "sale.order"
    domain = [("state", "=", "sale")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_supplier(client):
    model = "res.partner"
    domain = [("supplier", "=", True)]
    return search_browse(client, model, domain, random_pick=True)


def find_random_customer(client):
    model = "res.partner"
    domain = [("customer", "=", True)]
    return search_browse(client, model, domain, random_pick=True)


def find_random_pricelist(client):
    model = "product.pricelist"
    domain = []
    return search_browse(client, model, domain, random_pick=True)


def find_random_template(client):
    model = "sale.quote.template"
    domain = []
    return search_browse(client, model, domain, random_pick=True)


def find_random_task(client):
    model = "project.task"
    domain = [("user_id", "=", False)]
    return search_browse(client, model, domain, random_pick=True)


def find_random_task_done(client):
    model = "project.task"
    domain = [("user_id", "!=", False), ("stage_id.name", "ilike", "work done")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_task_ready(client):
    model = "project.task"
    domain = [("user_id", "!=", False), ("stage_id.name", "ilike", "confirmed")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_vendor_bill_draft(client):
    model = "account.invoice"
    domain = [("type", "=", "in_invoice"), ("state", "=", "draft")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_vendor_bill_open(client):
    model = "account.invoice"
    domain = [("type", "=", "in_invoice"), ("state", "=", "open")]
    return search_browse(client, model, domain, random_pick=True)


def find_random_won_lead(client):
    model = "crm.lead"
    domain = [
        ("stage_id.name", "=", "Won"),
        ("partner_id", "!=", False),
        ("order_ids", "=", False),
    ]
    return search_browse(client, model, domain, random_pick=True)


def generate_street_address(client):
    # generates "random" address str based on time
    now = datetime.datetime.now()
    usec = now.strftime("%f")
    adr_num = int(usec[2:])
    if adr_num < 1000:
        adr_num += 1000
    adr_num = str(adr_num)
    sec = usec[0:2]
    fsec = sec[0]
    lsec = sec[1]
    if fsec == "0":
        if lsec == "0":
            sec = "1"
            lsec = "1"
        else:
            sec = lsec
    if fsec == "1":
        suff = "TH"
    elif lsec == "1":
        suff = "ST"
    elif lsec == "2":
        suff = "ND"
    elif lsec == "3":
        suff = "RD"
    else:
        suff = "TH"
    if int(fsec) < 3:
        adr_dir = "N"
    elif int(fsec) < 6:
        adr_dir = "W"
    elif int(fsec) < 8:
        adr_dir = "S"
    else:
        adr_dir = "E"
    adr_ln = adr_num + " " + adr_dir + " " + sec + suff + " STREET"
    return adr_ln
