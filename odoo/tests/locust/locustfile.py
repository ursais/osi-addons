# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from locust import between
from locustodoorpc.client import OdooRPCLocust
from tasks import account, crm, project, purchase, sale, stock


class AccountUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [account.AccountTaskSet]


class CRMUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [crm.CRMTaskSet]


class ProjectUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [project.ProjectTaskSet]


class PurchaseUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [purchase.PurchaseTaskSet]


class SaleUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [sale.SaleTaskSet]


class StockUser(OdooRPCLocust):
    wait_time = between(1, 15)
    weight = 10
    tasks = [stock.StockTaskSet]
