# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import operator

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

ops = {"=": operator.eq, "!=": operator.ne}


class RmaOrderLine(models.Model):
    _name = "rma.order.line"
    _description = "RMA"
    _inherit = ["mail.thread"]
    _order = "id desc"

    @api.model
    def _get_default_type(self):
        if "supplier" in self.env.context:
            return "supplier"
        return "customer"

    @api.model
    def _default_warehouse_id(self):
        rma_id = self.env.context.get("default_rma_id", False)
        warehouse = self.env["stock.warehouse"]
        if rma_id:
            rma = self.env["rma.order"].browse(rma_id)
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", rma.company_id.id)], limit=1
            )
        return warehouse

    @api.model
    def _default_location_id(self):
        wh = self._default_warehouse_id()
        return wh.lot_rma_id

    @api.onchange("partner_id")
    def _onchange_delivery_address(self):
        self.delivery_address_id = self.env["res.partner"].browse(
            self.partner_id.address_get(["delivery"])["delivery"]
        )

    @api.model
    def _get_in_pickings(self):
        # We consider an in move one where the first origin is outside
        # of the company and the final destination is outside. In case
        # of 2 or 3 step pickings, we should categorize as in shipments
        # even when they are technically internal transfers.
        pickings = self.env["stock.picking"]
        for move in self.move_ids:
            first_usage = move._get_first_usage()
            last_usage = move._get_last_usage()
            if last_usage == "internal" and first_usage != "internal":
                pickings |= move.picking_id
            elif last_usage == "supplier" and first_usage == "customer":
                pickings |= move.picking_id
        return pickings

    @api.model
    def _get_in_moves(self):
        moves = self.env["stock.move"]
        for move in self.move_ids:
            first_usage = move._get_first_usage()
            last_usage = move._get_last_usage()
            if last_usage == "internal" and first_usage != "internal":
                moves |= move
            elif last_usage == "supplier" and first_usage == "customer":
                moves |= move
        return moves

    @api.model
    def _get_out_pickings(self):
        pickings = self.env["stock.picking"]
        for move in self.move_ids:
            first_usage = move._get_first_usage()
            last_usage = move._get_last_usage()
            if first_usage in ("internal", "production") and last_usage in (
                "customer",
                "supplier",
            ):
                pickings |= move.picking_id
            elif last_usage == "customer" and first_usage == "supplier":
                pickings |= move.picking_id
        return pickings

    def _compute_in_shipment_count(self):
        for line in self:
            pickings = line._get_in_pickings()
            line.in_shipment_count = len(pickings)

    def _compute_out_shipment_count(self):
        for line in self:
            pickings = line._get_out_pickings()
            line.out_shipment_count = len(pickings)

    def _get_rma_move_qty(self, states, direction="in"):
        for rec in self:
            product_obj = self.env["uom.uom"]
            qty = 0.0
            if direction == "in":
                moves = rec.move_ids.filtered(
                    lambda m: m.state in states
                    and (
                        m.location_id.usage == "supplier"
                        or m.location_id.usage == "customer"
                    )
                    and (
                        m.location_dest_id.usage == "internal"
                        or m.location_dest_id.usage == "supplier"
                    )
                )
            elif direction == "out":
                moves = rec.move_ids.filtered(
                    lambda m: m.state in states
                    and (
                        m.location_dest_id.usage == "supplier"
                        or m.location_dest_id.usage == "customer"
                    )
                    and (
                        m.location_id.usage == "internal"
                        or m.location_id.usage == "supplier"
                    )
                )
            for move in moves:
                # If the move is part of a chain don't count it
                if direction == "out" and move.move_orig_ids:
                    continue
                elif direction == "in" and move.move_dest_ids:
                    continue
                qty += product_obj._compute_quantity(move.product_uom_qty, rec.uom_id)
            return qty

    @api.depends(
        "move_ids",
        "move_ids.state",
        "qty_received",
        "receipt_policy",
        "product_qty",
        "type",
    )
    def _compute_qty_to_receive(self):
        for rec in self:
            rec.qty_to_receive = 0.0
            if rec.receipt_policy == "ordered":
                rec.qty_to_receive = rec.product_qty - rec.qty_received
            elif rec.receipt_policy == "delivered":
                rec.qty_to_receive = rec.qty_delivered - rec.qty_received

    @api.depends(
        "move_ids",
        "move_ids.state",
        "delivery_policy",
        "product_qty",
        "type",
        "qty_delivered",
        "qty_received",
    )
    def _compute_qty_to_deliver(self):
        for rec in self:
            rec.qty_to_deliver = 0.0
            if rec.delivery_policy == "ordered":
                rec.qty_to_deliver = rec.product_qty - rec.qty_delivered
            elif rec.delivery_policy == "received":
                rec.qty_to_deliver = rec.qty_received - rec.qty_delivered

    @api.depends("move_ids", "move_ids.state", "type")
    def _compute_qty_incoming(self):
        for rec in self:
            qty = rec._get_rma_move_qty(
                ("draft", "confirmed", "assigned"), direction="in"
            )
            rec.qty_incoming = qty

    @api.depends("move_ids", "move_ids.state", "type")
    def _compute_qty_received(self):
        for rec in self:
            qty = rec._get_rma_move_qty("done", direction="in")
            rec.qty_received = qty

    @api.depends("move_ids", "move_ids.state", "type")
    def _compute_qty_outgoing(self):
        for rec in self:
            qty = rec._get_rma_move_qty(
                ("draft", "confirmed", "assigned"), direction="out"
            )
            rec.qty_outgoing = qty

    @api.depends("move_ids", "move_ids.state", "type")
    def _compute_qty_delivered(self):
        for rec in self:
            qty = rec._get_rma_move_qty("done", direction="out")
            rec.qty_delivered = qty

    @api.model
    def _get_supplier_rma_qty(self):
        return sum(
            self.supplier_rma_line_ids.filtered(lambda r: r.state != "cancel").mapped(
                "product_qty"
            )
        )

    @api.depends(
        "customer_to_supplier",
        "supplier_rma_line_ids",
        "move_ids",
        "move_ids.state",
        "qty_received",
        "receipt_policy",
        "product_qty",
        "type",
    )
    def _compute_qty_supplier_rma(self):
        for rec in self:
            if rec.customer_to_supplier:
                supplier_rma_qty = rec._get_supplier_rma_qty()
                rec.qty_to_supplier_rma = rec.product_qty - supplier_rma_qty
                rec.qty_in_supplier_rma = supplier_rma_qty
            else:
                rec.qty_to_supplier_rma = 0.0
                rec.qty_in_supplier_rma = 0.0

    def _compute_rma_line_count(self):
        for rec in self.filtered(lambda r: r.type == "customer"):
            rec.rma_line_count = len(rec.supplier_rma_line_ids)
        for rec in self.filtered(lambda r: r.type == "supplier"):
            rec.rma_line_count = len(rec.customer_rma_id)

    @api.model
    def _default_date_rma(self):
        return fields.Datetime.now()

    delivery_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner delivery address",
        help="This address will be used to deliver repaired or replacement "
        "products.",
    )
    rma_id = fields.Many2one(
        comodel_name="rma.order",
        string="RMA Group",
        tracking=True,
        readonly=True,
    )
    name = fields.Char(
        string="Reference",
        required=True,
        default="/",
        help="Add here the supplier RMA #. Otherwise an internal code is" " assigned.",
        copy=False,
    )
    description = fields.Text()
    conditions = fields.Html(string="Terms and conditions")
    origin = fields.Char(
        string="Source Document",
        help="Reference of the document that produced this rma.",
    )
    date_rma = fields.Datetime(
        string="Order Date", index=True, default=lambda self: self._default_date_rma()
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("done", "Done"),
            ("canceled", "Canceled"),
        ],
        default="draft",
        tracking=True,
    )
    operation_id = fields.Many2one(
        comodel_name="rma.operation",
        required=True,
        readonly=False,
        tracking=True,
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
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        store=True,
        tracking=True,
    )
    sequence = fields.Integer(
        default=10, help="Gives the sequence of this line when displaying the rma."
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        ondelete="restrict",
        required=True,
    )
    product_tracking = fields.Selection(related="product_id.tracking")
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial Number",
    )
    product_qty = fields.Float(
        string="Return Qty",
        copy=False,
        default=1.0,
        digits="Product Unit of Measure",
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        required=True,
        compute="_compute_uom_id",
        precompute=True,
        store=True,
    )
    price_unit = fields.Monetary(
        string="Unit cost",
        help="Unit cost of the items under RMA",
    )
    in_shipment_count = fields.Integer(
        compute="_compute_in_shipment_count", string="# of Shipments"
    )
    out_shipment_count = fields.Integer(
        compute="_compute_out_shipment_count", string="# of Deliveries"
    )
    move_ids = fields.One2many(
        "stock.move", "rma_line_id", string="Stock Moves", readonly=True, copy=False
    )
    reference_move_id = fields.Many2one(
        comodel_name="stock.move",
        string="Originating Stock Move",
        copy=False,
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    type = fields.Selection(
        selection=[("customer", "Customer"), ("supplier", "Supplier")],
        required=True,
        default=lambda self: self._get_default_type(),
        readonly=True,
    )
    customer_to_supplier = fields.Boolean(
        "The customer will send to the supplier",
    )
    supplier_to_customer = fields.Boolean(
        "The supplier will send to the customer",
    )
    receipt_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
        ],
        required=True,
        default="no",
        readonly=False,
    )
    delivery_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        required=True,
        default="no",
        readonly=False,
        ondelete="cascade",
    )
    in_route_id = fields.Many2one(
        "stock.route",
        string="Inbound Route",
        required=True,
        domain=[("rma_selectable", "=", True)],
        compute="_compute_in_route_id",
        precompute=True,
        store=True,
    )
    out_route_id = fields.Many2one(
        "stock.route",
        string="Outbound Route",
        required=True,
        domain=[("rma_selectable", "=", True)],
        compute="_compute_out_route_id",
        precompute=True,
        store=True,
    )
    in_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Inbound Warehouse",
        required=True,
        default=lambda self: self._default_warehouse_id(),
    )
    out_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Outbound Warehouse",
        required=True,
        default=lambda self: self._default_warehouse_id(),
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Send To This Company Location",
        required=True,
        default=lambda self: self._default_location_id(),
    )
    customer_rma_id = fields.Many2one(
        "rma.order.line", string="Customer RMA line", ondelete="cascade"
    )
    supplier_rma_line_ids = fields.One2many("rma.order.line", "customer_rma_id")
    rma_line_count = fields.Integer(
        compute="_compute_rma_line_count", string="# of RMA lines associated"
    )
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
    qty_to_receive = fields.Float(
        digits="Product Unit of Measure",
        compute="_compute_qty_to_receive",
        store=True,
    )
    qty_incoming = fields.Float(
        string="Incoming Qty",
        copy=False,
        readonly=True,
        digits="Product Unit of Measure",
        compute="_compute_qty_incoming",
        store=True,
    )
    qty_received = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        compute="_compute_qty_received",
        store=True,
    )
    qty_to_deliver = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_to_deliver",
        store=True,
    )
    qty_outgoing = fields.Float(
        string="Outgoing Qty",
        copy=False,
        readonly=True,
        digits="Product Unit of Measure",
        compute="_compute_qty_outgoing",
        store=True,
    )
    qty_delivered = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_delivered",
        store=True,
    )
    qty_to_supplier_rma = fields.Float(
        string="Qty to send to Supplier RMA",
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_supplier_rma",
        store=True,
    )
    qty_in_supplier_rma = fields.Float(
        string="Qty in Supplier RMA",
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_supplier_rma",
        store=True,
    )
    under_warranty = fields.Boolean(string="Under Warranty?")

    def _prepare_rma_line_from_stock_move(self, sm, lot=False):
        if not self.type:
            self.type = self._get_default_type()
        if self.type == "customer":
            operation = (
                sm.product_id.rma_customer_operation_id
                or sm.product_id.categ_id.rma_customer_operation_id
            )
        else:
            operation = (
                sm.product_id.rma_supplier_operation_id
                or sm.product_id.categ_id.rma_supplier_operation_id
            )

        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", self.type)], limit=1
            )
            if not operation:
                raise ValidationError(_("Please define an operation first."))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define an RMA route."))

        if (
            not operation.in_warehouse_id
            or not operation.out_warehouse_id
            or not (
                operation.in_warehouse_id.lot_rma_id
                or operation.out_warehouse_id.lot_rma_id
            )
        ):
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.company_id.id), ("lot_rma_id", "!=", False)],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a default RMA location.")
                )

        data = {
            "product_id": sm.product_id.id,
            "lot_id": lot and lot.id or False,
            "origin": sm.picking_id.name or sm.name,
            "uom_id": sm.product_uom.id,
            "product_qty": sm.product_uom_qty,
            "delivery_address_id": sm.picking_id.partner_id.id,
            "operation_id": operation.id,
            "receipt_policy": operation.receipt_policy,
            "delivery_policy": operation.delivery_policy,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or operation.out_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
        }
        return data

    @api.onchange("reference_move_id")
    def _onchange_reference_move_id(self):
        self.ensure_one()
        sm = self.reference_move_id
        if not sm:
            return
        if sm.move_line_ids.lot_id:
            if len(sm.move_line_ids.lot_id) > 1:
                raise UserError(_("To manage lots use RMA groups."))
            else:
                data = self._prepare_rma_line_from_stock_move(
                    sm, lot=sm.move_line_ids.lot_id[0]
                )
                self.update(data)
        else:
            data = self._prepare_rma_line_from_stock_move(sm, lot=False)
            self.update(data)
        self._remove_other_data_origin("reference_move_id")

    @api.constrains("reference_move_id", "partner_id")
    def _check_move_partner(self):
        for rec in self:
            if (
                rec.reference_move_id
                and rec.reference_move_id.picking_id.partner_id != rec.partner_id
            ):
                raise ValidationError(
                    _(
                        "RMA customer and originating stock move customer "
                        "doesn't match."
                    )
                )

    def _remove_other_data_origin(self, exception):
        if not exception == "reference_move_id":
            self.reference_move_id = False
        return True

    def _check_lot_assigned(self):
        for rec in self:
            if rec.product_id.tracking == "serial" and rec.product_qty != 1:
                raise ValidationError(
                    _(
                        "Product %s has serial tracking configuration, "
                        "quantity to receive should be 1"
                    )
                    % (rec.product_id.display_name)
                )

    def action_rma_to_approve(self):
        self._check_lot_assigned()
        self.write({"state": "to_approve"})
        for rec in self:
            if rec.product_id.rma_approval_policy == "one_step":
                rec.action_rma_approve()
        return True

    def action_rma_draft(self):
        self.write({"state": "draft"})
        return True

    def action_rma_approve(self):
        self.write({"state": "approved"})
        return True

    def action_rma_done(self):
        self.write({"state": "done"})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "/":
                if self.env.context.get("supplier"):
                    vals["name"] = self.env["ir.sequence"].next_by_code(
                        "rma.order.line.supplier"
                    )
                else:
                    vals["name"] = self.env["ir.sequence"].next_by_code(
                        "rma.order.line.customer"
                    )
        return super().create(vals_list)

    def check_cancel(self):
        for move in self.move_ids:
            if move.state == "done":
                raise UserError(
                    _("Unable to cancel %s as some receptions have already been done.")
                    % (self.name)
                )

    def action_rma_cancel(self):
        for order in self:
            order.check_cancel()
            order.write({"state": "canceled"})
            order.move_ids._action_cancel()
            shipments = order._get_in_pickings()
            shipments |= order._get_out_pickings()
            for ship in shipments:
                ship.action_cancel()
        return True

    def _get_price_unit(self):
        """The price unit corresponds to the cost of that product"""
        self.ensure_one()
        if self.reference_move_id:
            price_unit = self.reference_move_id.price_unit
        else:
            price_unit = self.product_id.with_company(self.company_id).standard_price
        return price_unit

    @api.onchange("product_id")
    def _onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.uom_id = self.product_id.uom_id.id
        if not self.type:
            self.type = self._get_default_type()
        self.price_unit = self._get_price_unit()
        if self.type == "customer":
            self.operation_id = (
                self.product_id.rma_customer_operation_id
                or self.product_id.categ_id.rma_customer_operation_id
            )
        else:
            self.operation_id = (
                self.product_id.rma_supplier_operation_id
                or self.product_id.categ_id.rma_supplier_operation_id
            )
        if self.lot_id.product_id != self.product_id:
            self.lot_id = False
        return result

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = {}
        if not self.operation_id:
            return result
        self.receipt_policy = self.operation_id.receipt_policy
        self.delivery_policy = self.operation_id.delivery_policy
        self.customer_to_supplier = (
            self.rma_id.customer_to_supplier or self.operation_id.customer_to_supplier
        )
        self.supplier_to_customer = (
            self.rma_id.supplier_to_customer or self.operation_id.supplier_to_customer
        )
        self.in_warehouse_id = (
            self.rma_id.in_warehouse_id or self.operation_id.in_warehouse_id
        )
        self.out_warehouse_id = (
            self.rma_id.out_warehouse_id or self.operation_id.out_warehouse_id
        )
        self.location_id = (
            self.rma_id.location_id
            or self.operation_id.location_id
            or self.in_warehouse_id.lot_rma_id
        )
        self.in_route_id = self.rma_id.in_route_id or self.operation_id.in_route_id
        self.out_route_id = self.rma_id.out_route_id or self.operation_id.out_route_id
        return result

    @api.depends("operation_id")
    def _compute_in_route_id(self):
        for rec in self:
            rec.in_route_id = rec.operation_id.in_route_id

    @api.depends("operation_id")
    def _compute_out_route_id(self):
        for rec in self:
            rec.out_route_id = rec.operation_id.out_route_id

    @api.onchange("customer_to_supplier", "type")
    def _onchange_receipt_policy(self):
        if self.type == "supplier" and self.customer_to_supplier:
            self.receipt_policy = "no"
        elif self.type == "customer" and self.supplier_to_customer:
            self.delivery_policy = "no"

    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        product = self.lot_id.product_id
        if product:
            self.product_id = product

    @api.depends("product_id")
    def _compute_uom_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id

    def action_view_in_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        shipments = self.env["stock.picking"]
        for line in self:
            shipments |= line._get_in_pickings()
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result["domain"] = "[('id', 'in', " + str(shipments.ids) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = shipments.ids[0]
        return result

    def action_view_out_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        shipments = self.env["stock.picking"]
        for line in self:
            shipments |= line._get_out_pickings()
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result["domain"] = "[('id', 'in', " + str(shipments.ids) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = shipments.ids[0]
        return result

    def action_view_rma_lines(self):
        if self.type == "customer":
            # from customer we link to supplier rma
            action = self.env.ref("rma.action_rma_supplier_lines")
            rma_lines = self.supplier_rma_line_ids.ids
            res = self.env.ref("rma.view_rma_line_supplier_form", False)
        else:
            # from supplier we link to customer rma
            action = self.env.ref("rma.action_rma_customer_lines")
            rma_lines = self.customer_rma_id.ids
            res = self.env.ref("rma.view_rma_line_form", False)
        result = action.sudo().read()[0]
        # choose the view_mode accordingly
        if rma_lines and len(rma_lines) != 1:
            result["domain"] = rma_lines.ids
        elif len(rma_lines) == 1:
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = rma_lines[0]
        return result

    @api.constrains("partner_id", "rma_id")
    def _check_partner_id(self):
        if self.rma_id and self.partner_id != self.rma_id.partner_id:
            raise ValidationError(
                _("Group partner and RMA's partner must be the same.")
            )
