# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RmaOrder(models.Model):
    _name = "rma.order"
    _description = "RMA Group"
    _inherit = ["mail.thread"]
    _order = "id desc"

    @api.model
    def _get_default_type(self):
        if "supplier" in self.env.context:
            return "supplier"
        return "customer"

    def _compute_in_shipment_count(self):
        for rec in self:
            pickings = self.env["stock.picking"]
            for line in rec.rma_line_ids:
                pickings |= line._get_in_pickings()
            rec.in_shipment_count = len(pickings)

    def _compute_out_shipment_count(self):
        for rec in self:
            pickings = self.env["stock.picking"]
            for line in rec.rma_line_ids:
                pickings |= line._get_out_pickings()
            rec.out_shipment_count = len(pickings)

    def _compute_supplier_line_count(self):
        self.supplier_line_count = len(
            self.rma_line_ids.filtered(lambda r: r.supplier_rma_line_ids)
        )

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec._get_valid_lines())

    @api.depends("rma_line_ids", "rma_line_ids.state")
    def _compute_state(self):
        for rec in self:
            state = "draft"
            if rec.rma_line_ids:
                states = set(rec.rma_line_ids.mapped("state"))
                if states == {"cancel"}:
                    state = "cancel"
                elif "draft" in states:
                    state = "draft"
                elif "to_approved" in states:
                    state = "to_approved"
                elif "approved" in states:
                    state = "approved"
                else:
                    state = "done"
            rec.state = state

    @api.model
    def _default_date_rma(self):
        return datetime.now()

    @api.model
    def _default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        return warehouse

    name = fields.Char(string="Group Number", index=True, copy=False)
    type = fields.Selection(
        [("customer", "Customer"), ("supplier", "Supplier")],
        required=True,
        default=lambda self: self._get_default_type(),
        readonly=True,
    )
    reference = fields.Char(
        string="Partner Reference", help="The partner reference of this RMA order."
    )
    description = fields.Text()
    comment = fields.Text("Additional Information")
    date_rma = fields.Datetime(
        compute="_compute_date_rma",
        inverse="_inverse_date_rma",
        string="Order Date",
        index=True,
        default=lambda self: self._default_date_rma(),
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", required=True
    )
    rma_line_ids = fields.One2many("rma.order.line", "rma_id", string="RMA lines")
    in_shipment_count = fields.Integer(
        compute="_compute_in_shipment_count", string="# of Shipments"
    )
    out_shipment_count = fields.Integer(
        compute="_compute_out_shipment_count", string="# of Outgoing Shipments"
    )
    line_count = fields.Integer(compute="_compute_line_count", string="# of RMA lines")
    supplier_line_count = fields.Integer(
        compute="_compute_supplier_line_count", string="# of Supplier RMAs"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    assigned_to = fields.Many2one(
        comodel_name="res.users",
        tracking=True,
        default=lambda self: self.env.uid,
    )
    requested_by = fields.Many2one(
        comodel_name="res.users",
        tracking=True,
        default=lambda self: self.env.uid,
    )
    in_route_id = fields.Many2one(
        "stock.route",
        string="Inbound Route",
        domain=[("rma_selectable", "=", True)],
    )
    out_route_id = fields.Many2one(
        "stock.route",
        string="Outbound Route",
        domain=[("rma_selectable", "=", True)],
    )
    in_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Inbound Warehouse",
        required=False,
        default=_default_warehouse_id,
    )
    out_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Outbound Warehouse",
        required=False,
        default=_default_warehouse_id,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Send To This Company Location",
    )
    customer_to_supplier = fields.Boolean("The customer will send to the supplier")
    supplier_to_customer = fields.Boolean("The supplier will send to the customer")
    supplier_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier Address",
        help="Address of the supplier in case of Customer RMA operation " "dropship.",
    )
    customer_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer Address",
        help="Address of the customer in case of Supplier RMA operation " "dropship.",
    )
    state = fields.Selection(
        compute=_compute_state,
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        store=True,
    )
    operation_default_id = fields.Many2one(
        comodel_name="rma.operation",
        required=False,
        string="Default Operation Type",
    )

    @api.onchange(
        "operation_default_id",
    )
    def _onchange_operation(self):
        if self.operation_default_id:
            self.in_warehouse_id = self.operation_default_id.in_warehouse_id
            self.out_warehouse_id = self.operation_default_id.out_warehouse_id
            self.location_id = (
                self.operation_default_id.location_id or self.in_warehouse_id.lot_rma_id
            )
            self.customer_to_supplier = self.operation_default_id.customer_to_supplier
            self.supplier_to_customer = self.operation_default_id.supplier_to_customer
            self.in_route_id = self.operation_default_id.in_route_id
            self.out_route_id = self.operation_default_id.out_route_id

    @api.depends("rma_line_ids.date_rma")
    def _compute_date_rma(self):
        """If all order line have same date set date_rma.
        If no lines, respect value given by the user.
        """
        for rma in self:
            if rma.rma_line_ids:
                date_rma = rma.rma_line_ids[0].date_rma or False
                for rma_line in rma.rma_line_ids:
                    if rma_line.date_rma != date_rma:
                        date_rma = False
                        break
                rma.date_rma = date_rma

    def _inverse_date_rma(self):
        """When set date_rma set date_rma on all order lines"""
        for po in self:
            if po.date_rma:
                po.rma_line_ids.write({"date_rma": po.date_rma})

    @api.constrains("partner_id", "rma_line_ids")
    def _check_partner_id(self):
        if self.rma_line_ids and self.partner_id != self.mapped(
            "rma_line_ids.partner_id"
        ):
            raise UserError(_("Group partner and RMA's partner must be the same."))
        if len(self.mapped("rma_line_ids.partner_id")) > 1:
            raise UserError(_("All grouped RMA's should have same partner."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get("supplier") or vals.get("type") == "supplier":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "rma.order.supplier"
                )
            else:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "rma.order.customer"
                )
        return super().create(vals_list)

    def _view_shipments(self, result, shipments):
        # choose the view_mode accordingly
        if len(shipments) > 1:
            result["domain"] = [("id", "in", shipments.ids)]
        elif len(shipments) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = shipments.ids[0]
        return result

    def action_view_in_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        shipments = self.env["stock.picking"]
        for line in self.rma_line_ids:
            shipments |= line._get_in_pickings()
        return self._view_shipments(result, shipments)

    def action_view_out_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        shipments = self.env["stock.picking"]
        for line in self.rma_line_ids:
            shipments |= line._get_out_pickings()
        return self._view_shipments(result, shipments)

    def _get_valid_lines(self):
        """:return: A recordset of rma lines."""
        self.ensure_one()
        return self.rma_line_ids

    def action_view_lines(self):
        if self.type == "customer":
            action = self.env.ref("rma.action_rma_customer_lines")
            res = self.env.ref("rma.view_rma_line_form", False)
        else:
            action = self.env.ref("rma.action_rma_supplier_lines")
            res = self.env.ref("rma.view_rma_line_supplier_form", False)
        result = action.sudo().read()[0]
        lines = self._get_valid_lines()
        # choose the view_mode accordingly
        if len(lines.ids) != 1:
            result["domain"] = [("id", "in", lines.ids)]
        else:
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = lines.id
        result["context"] = {}
        return result

    def action_view_supplier_lines(self):
        action = self.env.ref("rma.action_rma_supplier_lines")
        result = action.sudo().read()[0]
        lines = self.rma_line_ids
        for line_id in lines:
            related_lines = [line.id for line in line_id.supplier_rma_line_ids]
            # choose the view_mode accordingly
            if len(related_lines) != 1:
                result["domain"] = [("id", "in", related_lines)]
            else:
                res = self.env.ref("rma.view_rma_line_supplier_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = related_lines[0]
        return result

    def action_rma_to_approve(self):
        return self.rma_line_ids.action_rma_to_approve()

    def action_rma_draft(self):
        return self.rma_line_ids.action_rma_draft()

    def action_rma_approve(self):
        return self.rma_line_ids.action_rma_approve()

    def action_rma_done(self):
        return self.rma_line_ids.action_rma_done()

    def action_rma_cancel(self):
        return self.rma_line_ids.action_rma_cancel()

    @api.onchange("in_warehouse_id")
    def _onchange_in_warehouse_id(self):
        if self.in_warehouse_id and self.rma_line_ids:
            for rma_line in self.rma_line_ids:
                rma_line.in_warehouse_id = self.in_warehouse_id.id
                rma_line.location_id = self.in_warehouse_id.lot_rma_id.id

    @api.onchange("customer_to_supplier", "supplier_address_id")
    def _onchange_customer_to_supplier(self):
        if self.type == "customer" and self.rma_line_ids:
            for rma_line in self.rma_line_ids:
                rma_line.customer_to_supplier = self.customer_to_supplier
                rma_line.supplier_address_id = self.supplier_address_id.id

    @api.onchange("supplier_to_customer", "customer_address_id")
    def _onchange_supplier_to_customer(self):
        if self.type == "supplier" and self.rma_line_ids:
            for rma_line in self.rma_line_ids:
                rma_line.supplier_to_customer = self.supplier_to_customer
                rma_line.customer_address_id = self.customer_address_id.id
