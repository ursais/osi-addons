# Copyright 2017-18 ForgeFlow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOperation(models.Model):
    _name = "rma.operation"
    _description = "RMA Operation"

    @api.model
    def _default_warehouse_id(self):
        company_id = self.env.user.company_id.id
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", company_id)], limit=1
        )
        return warehouse

    @api.model
    def _default_customer_location_id(self):
        return self.env.ref("stock.stock_location_customers") or False

    @api.model
    def _default_supplier_location_id(self):
        return self.env.ref("stock.stock_location_suppliers") or False

    @api.model
    def _default_routes(self):
        op_type = self.env.context.get("default_type")
        if op_type == "customer":
            return self.env.ref("rma.route_rma_customer")
        elif op_type == "supplier":
            return self.env.ref("rma.route_rma_supplier")

    name = fields.Char("Description", required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    receipt_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
        ],
        default="no",
    )
    delivery_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )
    in_route_id = fields.Many2one(
        comodel_name="stock.route",
        string="Inbound Route",
        domain=[("rma_selectable", "=", True)],
        default=lambda self: self._default_routes(),
    )
    out_route_id = fields.Many2one(
        comodel_name="stock.route",
        string="Outbound Route",
        domain=[("rma_selectable", "=", True)],
        default=lambda self: self._default_routes(),
    )
    customer_to_supplier = fields.Boolean(
        string="The customer will send to the supplier"
    )
    supplier_to_customer = fields.Boolean(
        string="The supplier will send to the customer"
    )
    in_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Inbound Warehouse",
        default=lambda self: self._default_warehouse_id(),
    )
    out_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Outbound Warehouse",
        default=lambda self: self._default_warehouse_id(),
    )
    location_id = fields.Many2one("stock.location", "Send To This Company Location")
    type = fields.Selection(
        [("customer", "Customer"), ("supplier", "Supplier")],
        string="Used in RMA of this type",
        required=True,
    )
    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line", inverse_name="operation_id", string="RMA lines"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
