# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    def _compute_purchase_count(self):
        for rec in self:
            purchase_line_count = self.env["purchase.order.line"].search(
                [("rma_line_id", "=", rec.id)]
            )
            rec.purchase_count = len(purchase_line_count.mapped("order_id"))

    def _compute_purchase_order_lines(self):
        for rec in self:
            purchase_list = []
            for line in self.env["purchase.order.line"].search(
                [("rma_line_id", "=", rec.id)]
            ):
                purchase_list.append(line.id)
            rec.purchase_order_line_ids = [(6, 0, purchase_list)]

    @api.depends("operation_id", "purchase_policy")
    def _compute_qty_purchase(self):
        for rec in self:
            rec.qty_purchased = rec._get_rma_purchased_qty()
            if rec.purchase_policy == "ordered":
                rec.qty_to_purchase = rec.product_qty - rec.qty_purchased
            elif rec.purchase_policy == "delivered":
                rec.qty_to_purchase = rec.qty_delivered - rec.qty_purchased
            else:
                rec.qty_to_purchase = 0.0

    purchase_count = fields.Integer(
        compute="_compute_purchase_count",
        string="# of Purchases",
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Originating Purchase Line",
        ondelete="restrict",
    )
    purchase_id = fields.Many2one(
        string="Source Purchase Order",
        related="purchase_order_line_id.order_id",
        readonly=True,
    )
    purchase_order_line_ids = fields.Many2many(
        comodel_name="purchase.order.line",
        relation="purchase_line_rma_line_rel",
        column1="rma_order_line_id",
        column2="purchase_order_line_id",
        string="Purchase Order Lines",
        compute="_compute_purchase_order_lines",
    )
    purchase_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
        ],
        default="no",
        required=True,
    )
    manual_purchase_line_ids = fields.One2many(
        comodel_name="purchase.order.line",
        inverse_name="rma_line_id",
        string="Manual Purchase Order Lines",
        readonly=True,
        copy=False,
    )
    qty_to_purchase = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_purchase",
    )
    qty_purchased = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_purchase",
    )

    @api.onchange("product_id", "partner_id")
    def _onchange_product_id(self):
        """Domain for purchase_order_line_id is computed here to make
        it dynamic."""
        res = super()._onchange_product_id()
        if not res.get("domain"):
            res["domain"] = {}
        domain = [
            "|",
            ("order_id.partner_id", "=", self.partner_id.id),
            ("order_id.partner_id", "child_of", self.partner_id.id),
        ]
        if self.product_id:
            domain.append(("product_id", "=", self.product_id.id))
        res["domain"]["purchase_order_line_id"] = domain
        return res

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        res = super()._onchange_operation_id()
        if self.operation_id:
            self.purchase_policy = self.operation_id.purchase_policy or "no"
        return res

    def _prepare_rma_line_from_po_line(self, line):
        self.ensure_one()
        if not self.type:
            self.type = self._get_default_type()
        if self.type == "customer":
            operation = (
                line.product_id.rma_customer_operation_id
                or line.product_id.categ_id.rma_customer_operation_id
            )
        else:
            operation = (
                line.product_id.rma_supplier_operation_id
                or line.product_id.categ_id.rma_supplier_operation_id
            )
        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", self.type)], limit=1
            )
            if not operation:
                raise ValidationError(_("Please define an operation first"))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.location.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define a rma route."))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.company_id.id), ("lot_rma_id", "!=", False)],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a default rma location.")
                )

        data = {
            "product_id": line.product_id.id,
            "origin": line.order_id.name,
            "uom_id": line.product_uom.id,
            "operation_id": operation.id,
            "product_qty": line.product_qty,
            "price_unit": line.currency_id._convert(
                line.price_unit,
                line.currency_id,
                self.env.user.company_id,
                fields.Date.today(),
                round=False,
            ),
            "in_route_id": operation.in_route_id.id or route,
            "out_route_id": operation.out_route_id.id or route,
            "receipt_policy": operation.receipt_policy,
            "currency_id": line.currency_id.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
            "refund_policy": operation.refund_policy,
            "delivery_policy": operation.delivery_policy,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
        }
        return data

    @api.onchange("purchase_order_line_id")
    def _onchange_purchase_order_line_id(self):
        if not self.purchase_order_line_id:
            return
        data = self._prepare_rma_line_from_po_line(self.purchase_order_line_id)
        self.update(data)
        self._remove_other_data_origin("purchase_order_line_id")

    @api.constrains("purchase_order_line_id", "partner_id")
    def _check_purchase_partner(self):
        for rec in self:
            if (
                rec.purchase_order_line_id
                and rec.purchase_order_line_id.order_id.partner_id != rec.partner_id
            ):
                raise ValidationError(
                    _(
                        "RMA customer and originating purchase line customer "
                        "doesn't match."
                    )
                )

    def _remove_other_data_origin(self, exception):
        res = super()._remove_other_data_origin(exception)
        if not exception == "purchase_order_line_id":
            self.purchase_order_line_id = False
        return res

    def action_view_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq")
        result = action.sudo().read()[0]
        orders = self.mapped("purchase_order_line_ids.order_id")
        result["domain"] = [("id", "in", orders.ids)]
        return result

    def action_rma_cancel(self):
        res = super().action_rma_cancel()
        for line in self:
            line.purchase_order_line_ids.mapped("order_id").button_cancel()
        return res

    def _get_rma_purchased_qty(self):
        self.ensure_one()
        qty = 0.0
        if self.type == "customer":
            return qty
        for line in self.purchase_order_line_ids.filtered(
            lambda p: p.state not in ("draft", "sent", "cancel")
        ):
            qty += self.uom_id._compute_quantity(line.product_qty, line.product_uom)
        return qty

    def _get_price_unit(self):
        self.ensure_one()
        price_unit = super()._get_price_unit()
        if self.purchase_order_line_id:
            moves = self.purchase_order_line_id.move_ids
            if moves:
                layers = moves.sudo().mapped("stock_valuation_layer_ids")
                if layers:
                    price_unit = sum(layers.mapped("value")) / sum(
                        layers.mapped("quantity")
                    )
        elif self.account_move_line_id.purchase_line_id:
            purchase_lines = self.account_move_line_id.purchase_line_id
            moves = purchase_lines.mapped("move_ids")
            if moves:
                layers = moves.sudo().mapped("stock_valuation_layer_ids")
                if layers:
                    price_unit = sum(layers.mapped("value")) / sum(
                        layers.mapped("quantity")
                    )
        return price_unit
