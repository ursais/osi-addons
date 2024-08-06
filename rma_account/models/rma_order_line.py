# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.model
    def _default_invoice_address(self):
        partner_id = self.env.context.get("partner_id")
        if partner_id:
            return self.env["res.partner"].browse(partner_id)
        return self.env["res.partner"]

    @api.depends(
        "move_line_ids", "move_line_ids.move_id.state", "refund_policy", "type"
    )
    def _compute_qty_refunded(self):
        for rec in self:
            rec.qty_refunded = sum(
                rec.refund_line_ids.filtered(
                    lambda i: i.move_id.state in ("posted")
                ).mapped("quantity")
            )

    @api.depends(
        "move_line_ids",
        "move_line_ids.move_id.state",
        "refund_policy",
        "move_ids",
        "move_ids.state",
        "type",
    )
    def _compute_qty_to_refund(self):
        qty = 0.0
        for res in self:
            if res.refund_policy == "ordered":
                qty = res.product_qty - res.qty_refunded
            elif res.refund_policy == "received":
                qty = res.qty_received - res.qty_refunded
            elif res.refund_policy == "delivered":
                qty = res.qty_delivered - res.qty_refunded
            res.qty_to_refund = qty

    def _compute_refund_count(self):
        for rec in self:
            rec.refund_count = len(rec.refund_line_ids.mapped("move_id"))

    invoice_address_id = fields.Many2one(
        "res.partner",
        string="Partner invoice address",
        default=lambda self: self._default_invoice_address(),
        help="Invoice address for current rma order.",
    )
    refund_count = fields.Integer(
        compute="_compute_refund_count", string="# of Refunds", default=0
    )
    account_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Originating Invoice Line",
        ondelete="restrict",
        index=True,
    )
    move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="rma_line_id",
        string="Journal Items",
        copy=False,
        index=True,
        readonly=True,
    )
    refund_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="rma_line_id",
        string="Refund Lines",
        domain=[
            ("move_id.move_type", "in", ["in_refund", "out_refund"]),
            ("display_type", "=", "product"),
        ],
        copy=False,
        index=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        "account.move",
        string="Source",
        related="account_move_line_id.move_id",
        index=True,
        readonly=True,
    )
    refund_policy = fields.Selection(
        [
            ("no", "No refund"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        required=True,
        default="no",
        readonly=False,
    )
    qty_to_refund = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_to_refund",
        store=True,
    )
    qty_refunded = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_refunded",
        store=True,
    )

    commercial_partner_id = fields.Many2one(
        "res.partner",
        string="Commercial Entity",
        store=True,
        readonly=True,
        compute="_compute_commercial_partner_id",
        ondelete="restrict",
    )

    @api.depends("partner_id")
    def _compute_commercial_partner_id(self):
        for rma_line in self:
            rma_line.commercial_partner_id = rma_line.partner_id.commercial_partner_id

    @api.onchange("product_id", "partner_id")
    def _onchange_product_id(self):
        """Domain for sale_line_id is computed here to make it dynamic."""
        res = super()._onchange_product_id()
        if not res.get("domain"):
            res["domain"] = {}
        if not self.product_id:
            domain = [
                "|",
                ("move_id.partner_id", "=", self.partner_id.id),
                ("move_id.partner_id", "child_of", self.partner_id.id),
                ("display_type", "=", "product"),
            ]
            res["domain"]["account_move_line_id"] = domain
        else:
            domain = [
                "&",
                "|",
                ("move_id.partner_id", "=", self.partner_id.id),
                ("move_id.partner_id", "child_of", self.partner_id.id),
                ("display_type", "=", "product"),
                ("product_id", "=", self.product_id.id),
            ]
            res["domain"]["account_move_line_id"] = domain
        return res

    def _prepare_rma_line_from_inv_line(self, line):
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
                raise ValidationError(_("Please define an rma route"))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.company_id.id), ("lot_rma_id", "!=", False)],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a" " default rma location")
                )
        data = {
            "product_id": line.product_id.id,
            "origin": line.move_id.name,
            "uom_id": line.product_uom_id.id,
            "operation_id": operation.id,
            "product_qty": line.quantity,
            "price_unit": line.move_id.currency_id._convert(
                line.price_unit,
                line.currency_id,
                line.company_id,
                line.date,
                round=False,
            ),
            "delivery_address_id": line.move_id.partner_id.id,
            "invoice_address_id": line.move_id.partner_id.id,
            "receipt_policy": operation.receipt_policy,
            "refund_policy": operation.refund_policy,
            "delivery_policy": operation.delivery_policy,
            "currency_id": line.currency_id.id,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
        }
        return data

    @api.onchange("account_move_line_id")
    def _onchange_account_move_line_id(self):
        if not self.account_move_line_id:
            return
        data = self._prepare_rma_line_from_inv_line(self.account_move_line_id)
        self.update(data)
        self._remove_other_data_origin("account_move_line_id")

    @api.constrains("account_move_line_id", "partner_id")
    def _check_invoice_partner(self):
        for rec in self:
            if (
                rec.account_move_line_id
                and rec.account_move_line_id.move_id.partner_id != rec.partner_id
            ):
                raise ValidationError(
                    _(
                        "RMA customer and originating invoice line customer "
                        "doesn't match."
                    )
                )

    def _remove_other_data_origin(self, exception):
        res = super()._remove_other_data_origin(exception)
        if not exception == "account_move_line_id":
            self.account_move_line_id = False
        return res

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super()._onchange_operation_id()
        if self.operation_id:
            self.refund_policy = self.operation_id.refund_policy or "no"
        return result

    @api.constrains("account_move_line_id")
    def _check_duplicated_lines(self):
        for line in self:
            matching_inv_lines = self.env["account.move.line"].search(
                [("id", "=", line.account_move_line_id.id)]
            )
            if len(matching_inv_lines) > 1:
                raise UserError(
                    _(
                        "There's an rma for the "
                        "invoice line %(arg1)s and invoice %(arg2)s",
                        arg1=line.account_move_line_id,
                        arg2=line.account_move_line_id.move_id,
                    )
                )
        return {}

    def action_view_invoice(self):
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", [self.account_move_line_id.move_id.id])],
            "name": "Originating Invoice",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }

    def action_view_refunds(self):
        moves = self.mapped("refund_line_ids.move_id")
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", moves.ids)],
            "name": "Refunds",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for rma in self:
            rma.display_name = f"{rma.name} {rma.product_id.name} qty:{rma.product_qty}"

    def _stock_account_anglo_saxon_reconcile_valuation(self):
        for rma in self:
            prod = rma.product_id
            if rma.product_id.valuation != "real_time":
                continue
            if not rma.company_id.anglo_saxon_accounting:
                continue
            product_accounts = prod.product_tmpl_id._get_product_accounts()
            if rma.type == "customer":
                product_interim_account = product_accounts["stock_output"]
            else:
                product_interim_account = product_accounts["stock_input"]
            if product_interim_account.reconcile:
                # Get the in and out moves
                amls = self.env["account.move.line"].search(
                    [
                        ("rma_line_id", "=", rma.id),
                        ("account_id", "=", product_interim_account.id),
                        ("parent_state", "=", "posted"),
                        ("reconciled", "=", False),
                    ]
                )
                amls |= rma.move_ids.mapped(
                    "stock_valuation_layer_ids.account_move_id.line_ids"
                )
                # Search for anglo-saxon lines linked to the product in the journal
                # entry.
                amls = amls.filtered(
                    lambda line,
                    prod=prod,
                    product_interim_account=product_interim_account: line.product_id
                    == prod
                    and line.account_id == product_interim_account
                    and not line.reconciled
                )
                # Reconcile.
                amls.reconcile()

    def _get_price_unit(self):
        self.ensure_one()
        price_unit = super()._get_price_unit()
        if self.reference_move_id:
            move = self.reference_move_id
            layers = move.sudo().stock_valuation_layer_ids
            if layers:
                price_unit = sum(layers.mapped("value")) / sum(
                    layers.mapped("quantity")
                )
                price_unit = price_unit
        elif self.account_move_line_id and self.type == "supplier":
            # We get the cost from the original invoice line
            price_unit = self.account_move_line_id.price_unit
        return price_unit

    def _refund_at_zero_cost(self):
        make_refund = (
            self.env["rma.refund"]
            .with_context(
                **{
                    "customer": True,
                    "active_ids": self.ids,
                    "active_model": "rma.order.line",
                }
            )
            .create({"description": "RMA Anglosaxon Regularisation"})
        )
        for item in make_refund.item_ids:
            item.qty_to_refund = item.line_id.qty_received - item.line_id.qty_refunded
        action_refund = make_refund.invoice_refund()
        refund_id = action_refund.get("res_id", False)
        if refund_id:
            refund = self.env["account.move"].browse(refund_id)
            refund._post()

    def _check_refund_zero_cost(self):
        """
        In the scenario where a company uses anglo-saxon accounting, if you receive
        products from a customer and don't expect to refund the customer but send a
        replacement unit you still need to create a debit entry on the
        Stock Interim (Delivered) account. In order to do this the best approach is
        to create a customer refund from the RMA, but set as free of charge
        (price unit = 0). The refund will be 0, but the Stock Interim (Delivered)
        account will be posted anyways.
        """
        # For some reason api.depends on qty_received is not working. Using the
        # _account_entry_move method in stock move as trigger then
        for rec in self.filtered(lambda line: line.operation_id.automated_refund):
            if rec.qty_received > rec.qty_refunded:
                rec._refund_at_zero_cost()
