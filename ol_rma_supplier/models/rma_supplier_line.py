# Import Odoo libs
from odoo import api, fields, models


class RmaSupplierLine(models.Model):
    """RMA Line Object to contain product information."""

    _name = "rma.supplier.order.line"
    _description = "RMA Supplier Line"

    # COLUMNS ######

    name = fields.Text(
        string="Description",
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        compute="_compute_product_uom",
        store=True,
        readonly=False,
        precompute=True,
        ondelete="restrict",
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
    )
    serial = fields.Char(string="serial")
    lot_ids = fields.Many2many(
        "stock.lot",
        string="Serial Numbers",
    )
    rma_order_id = fields.Many2one(
        "rma.supplier.order",
        string="RMA Reference",
        ondelete="cascade",
        required=True,
    )
    move_ids = fields.One2many(
        "stock.move",
        "rma_line_id",
        string="Stock Moves",
    )
    qty_delivered = fields.Float(
        string="Qty Delivery",
        compute="_compute_qty_delivered_received",
        compute_sudo=True,
        store=True,
        readonly=False,
        copy=False,
    )
    qty_received = fields.Float(
        "Qty Received",
        compute="_compute_qty_delivered_received",
        compute_sudo=True,
        store=True,
        readonly=False,
        copy=False,
    )
    note = fields.Text(string="Note")

    # END ##########
    # METHODS ##########

    @api.depends(
        "rma_order_id",
        "rma_order_id.name",
        "product_id",
        "product_id.name",
    )
    def _compute_name(self):
        for rma_line in self.sudo():
            name = "{} - {}".format(
                rma_line.rma_order_id.name,
                rma_line.name
                and rma_line.name.split("\n")[0]
                or rma_line.product_id.name,
            )
            rma_line.name = name

    @api.depends("product_id")
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (
                line.product_id.uom_id.id != line.product_uom.id
            ):
                line.product_uom = line.product_id.uom_id

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env["stock.move"]
        incoming_moves = self.env["stock.move"]

        moves = self.move_ids.filtered(
            lambda r: r.state != "cancel"
            and not r.scrapped
            and self.product_id == r.product_id
        )

        for move in moves:
            if move.location_dest_id.usage == "supplier":
                if not move.origin_returned_move_id or (
                    move.origin_returned_move_id and move.to_refund
                ):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "supplier":  # and move.to_refund:
                incoming_moves |= move

        return outgoing_moves, incoming_moves

    @api.depends(
        "move_ids.state",
        "move_ids.scrapped",
        "move_ids.quantity",
        "move_ids.product_uom",
    )
    def _compute_qty_delivered_received(self):
        for line in self:
            delivered_qty = 0.0
            received_qty = 0.0
            outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
            # raise UserError("%s, %s" % (outgoing_moves, incoming_moves))
            for move in outgoing_moves:
                if move.state == "done":
                    delivered_qty += move.product_uom._compute_quantity(
                        move.quantity, line.product_uom, rounding_method="HALF-UP"
                    )
            for move in incoming_moves:
                if move.state == "done":
                    received_qty += move.product_uom._compute_quantity(
                        move.quantity, line.product_uom, rounding_method="HALF-UP"
                    )
            line.qty_delivered = delivered_qty
            line.qty_received = received_qty

    # END ##########
