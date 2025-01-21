# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError


class RmaSupplier(models.Model):
    """RMA object specific for vendor RMA's."""

    _name = "rma.supplier.order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id DESC"
    _description = "RMA to Supplier"

    # FIELD DEFAULT METHOD ######

    @api.model
    def _default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        return warehouse

    # END ##########
    # COLUMNS ######

    name = fields.Char(
        string="RMA Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    rma_number = fields.Char(string="Supplier RMA#")
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        string="Delivery Address",
        compute="_compute_partner_shipping_id",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("complete", "Completed"),
            ("cancel", "Canceled"),
        ],
        default="draft",
        string="State",
        required=True,
    )
    note = fields.Text("Note")
    line_ids = fields.One2many(
        "rma.supplier.order.line",
        "rma_supplier_order_ids",
        string="RMA Lines",
    )
    tag_ids = fields.Many2many(
        "rma.supplier.tag",
        string="Tags",
    )
    in_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="In Warehouse",
        required=True,
        default=_default_warehouse_id,
    )
    out_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Out Warehouse",
        required=True,
        default=_default_warehouse_id,
    )
    out_operation_id = fields.Many2one(
        "stock.picking.type",
        string="Out Operation",
        required=True,
    )
    out_location_id = fields.Many2one(
        "stock.location",
        string="Out Location",
        required=True,
    )
    in_operation_id = fields.Many2one(
        "stock.picking.type",
        string="In Operation",
        required=True,
    )
    in_location_id = fields.Many2one(
        "stock.location",
        string="In Location",
        required=True,
    )
    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Shipping Method",
    )
    out_transfer_ids = fields.One2many(
        "stock.picking",
        "rma_out_id",
        string="Out Transfers",
    )
    in_transfer_ids = fields.One2many(
        "stock.picking",
        "rma_in_id",
        string="In Transfers",
    )
    out_transfer_count = fields.Integer(
        string="Out Transfers",
        compute="_compute_out_transfer_count",
    )
    in_transfer_count = fields.Integer(
        string="In Transfers",
        compute="_compute_in_transfer_count",
    )
    receipt_status = fields.Selection(
        [
            ("pending", "Not Received"),
            ("partial", "Partially Received"),
            ("full", "Fully Received"),
        ],
        string="Receipt Status",
        compute="_compute_receipt_deliver_status",
        store=True,
    )
    deliver_status = fields.Selection(
        [
            ("pending", "Not Received"),
            ("partial", "Partially Received"),
            ("full", "Fully Received"),
        ],
        string="Deliver Status",
        compute="_compute_receipt_deliver_status",
        store=True,
    )
    product_id = fields.Many2one(
        "product.product",
        related="line_ids.product_id",
        string="Product",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # END ##########
    # METHODS ##########

    @api.depends("out_transfer_ids")
    def _compute_out_transfer_count(self):
        for rma in self:
            rma.out_transfer_count = len(rma.out_transfer_ids)

    @api.depends("in_transfer_ids")
    def _compute_in_transfer_count(self):
        for rma in self:
            rma.in_transfer_count = len(rma.in_transfer_ids)

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = (
                order.partner_id.address_get(["delivery"])["delivery"]
                if order.partner_id
                else False
            )

    @api.depends(
        "in_transfer_ids",
        "in_transfer_ids.state",
        "out_transfer_ids",
        "out_transfer_ids.state",
    )
    def _compute_receipt_deliver_status(self):
        for order in self:
            # Compute Deliver Status
            if not order.out_transfer_ids or all(
                p.state == "cancel" for p in order.out_transfer_ids
            ):
                order.deliver_status = False
            elif all(p.state in ["done", "cancel"] for p in order.out_transfer_ids):
                order.deliver_status = "full"
            elif any(p.state == "done" for p in order.out_transfer_ids):
                order.deliver_status = "partial"
            else:
                order.deliver_status = "pending"

            # Compute Receipt Status
            if not order.in_transfer_ids or all(
                p.state == "cancel" for p in order.in_transfer_ids
            ):
                order.receipt_status = False
            elif all(p.state in ["done", "cancel"] for p in order.in_transfer_ids):
                order.receipt_status = "full"
            elif any(p.state == "done" for p in order.in_transfer_ids):
                order.receipt_status = "partial"
            else:
                order.receipt_status = "pending"

    @api.onchange("in_warehouse_id")
    def _onchange_in_warehouse_id(self):
        if self.in_warehouse_id:
            self.in_operation_id = self.in_warehouse_id.rma_sup_in_type_id.id
            self.in_location_id = self.in_warehouse_id.lot_rma_id.id

    @api.onchange("out_warehouse_id")
    def _onchange_out_warehouse_id(self):
        if self.out_warehouse_id:
            self.out_operation_id = self.out_warehouse_id.rma_sup_out_type_id.id
            self.out_location_id = self.out_warehouse_id.lot_rma_id.id

    def action_view_out_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        if self.out_transfer_count == 1:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = self.out_transfer_ids.id
        else:
            action["domain"] = [("id", "in", self.out_transfer_ids.ids)]
        return action

    def action_view_in_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        if self.in_transfer_count == 1:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = self.in_transfer_ids.id
        else:
            action["domain"] = [("id", "in", self.in_transfer_ids.ids)]
        return action

    def action_confirm(self):
        for rma in self:
            # Raise error if user tries to confirm an RMA without product(s)
            if not rma.line_ids:
                raise UserError("Please add at least one product to RMA.")

            # Create out transfer
            out_transfer = self.env["stock.picking"].create(
                {
                    "partner_id": rma.partner_id.id,
                    "picking_type_id": rma.out_operation_id.id,
                    "location_id": rma.out_location_id.id,
                    "location_dest_id": rma.partner_id.property_stock_supplier.id
                    or rma.in_operation_id.default_location_dest_id.id,
                    "carrier_id": rma.carrier_id.id,
                    "move_ids_without_package": [
                        (
                            0,
                            0,
                            {
                                "product_id": line.product_id.id,
                                "product_uom_qty": line.quantity,
                                "product_uom": line.product_id.uom_id.id,
                                "name": line.product_id.name,
                                "location_id": rma.out_location_id.id,
                                "location_dest_id": rma.partner_id.property_stock_supplier.id
                                or rma.in_operation_id.default_location_dest_id.id,
                                "rma_supplier_line_id": line.id,
                                "origin": rma.name,
                                "lot_ids": line.lot_ids.ids,
                            },
                        )
                        for line in rma.line_ids
                    ],
                    "rma_out_id": rma.id,
                }
            )
            rma.out_transfer_ids = [(4, out_transfer.id)]

            # Create in transfer
            in_transfer = self.env["stock.picking"].create(
                {
                    "partner_id": rma.partner_id.id,
                    "picking_type_id": rma.in_operation_id.id,
                    "location_id": rma.partner_id.property_stock_supplier.id
                    or rma.in_operation_id.default_location_src_id.id,
                    "location_dest_id": rma.in_location_id.id,
                    "move_ids_without_package": [
                        (
                            0,
                            0,
                            {
                                "product_id": line.product_id.id,
                                "product_uom_qty": line.quantity,
                                "product_uom": line.product_id.uom_id.id,
                                "name": line.product_id.name,
                                "location_id": rma.partner_id.property_stock_supplier.id
                                or rma.in_operation_id.default_location_src_id.id,
                                "location_dest_id": rma.in_location_id.id,
                                "rma_supplier_line_id": line.id,
                                "origin": rma.name,
                                "lot_ids": line.lot_ids.ids,
                            },
                        )
                        for line in rma.line_ids
                    ],
                    "rma_in_id": rma.id,
                }
            )
            rma.in_transfer_ids = [(4, in_transfer.id)]

            rma.state = "confirm"

    def action_cancel(self):
        for rma in self:
            # Cancel out transfers
            for out_transfer in rma.out_transfer_ids:
                if out_transfer.state not in ["done", "cancel"]:
                    out_transfer.action_cancel()

            # Cancel in transfers
            for in_transfer in rma.in_transfer_ids:
                if in_transfer.state not in ["done", "cancel"]:
                    in_transfer.action_cancel()

            rma.state = "cancel"

    def action_reset_to_draft(self):
        for rma in self:
            rma.state = "draft"

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("rma.supplier.order") or "New"
            )
        return super().create(vals)

    # END ##########
