# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaAddSale(models.TransientModel):
    _name = "rma_add_sale"
    _description = "Wizard to add rma lines from SO lines"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_obj = self.env["rma.order"]
        rma_id = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]
        if not rma_id:
            return res
        assert active_model == "rma.order", "Bad context propagation"

        rma = rma_obj.browse(rma_id)
        res["rma_id"] = rma.id
        res["partner_id"] = rma.partner_id.id
        res["sale_id"] = False
        res["sale_line_ids"] = False
        return res

    rma_id = fields.Many2one(
        comodel_name="rma.order", string="RMA Order", readonly=True
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", readonly=True
    )
    sale_id = fields.Many2one(comodel_name="sale.order", string="Order")
    sale_line_ids = fields.Many2many(
        "sale.order.line",
        "rma_add_sale_add_line_rel",
        "sale_line_id",
        "rma_add_sale_id",
        readonly=False,
        string="Sale Lines",
    )
    show_lot_filter = fields.Boolean(
        string="Show lot filter?",
        compute="_compute_lot_domain",
    )
    lot_domain_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Lots Domain",
        compute="_compute_lot_domain",
    )

    @api.depends(
        "sale_line_ids.move_ids.move_line_ids.lot_id",
    )
    def _compute_lot_domain(self):
        for rec in self:
            rec.lot_domain_ids = (
                rec.mapped("sale_line_ids.move_ids")
                .filtered(lambda x: x.state == "done")
                .mapped("move_line_ids.lot_id")
                .ids
            )
            rec.show_lot_filter = bool(rec.lot_domain_ids)

    lot_ids = fields.Many2many(comodel_name="stock.lot", string="Lots/Serials selected")

    def select_all(self):
        self.ensure_one()
        self.write(
            {
                "lot_ids": [(6, 0, self.lot_domain_ids.ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Sale Order"),
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "new",
        }

    def _prepare_rma_line_from_sale_order_line(
        self, line, product, quantity, uom_id=False, lot=None
    ):
        operation = self.rma_id.operation_default_id
        if not operation:
            operation = line.product_id.rma_customer_operation_id
            if not operation:
                operation = line.product_id.categ_id.rma_customer_operation_id
        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", self.rma_id.type)], limit=1
            )
            if not operation:
                raise ValidationError(_("Please define an operation first"))
        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.location.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define an rma route"))
        warehouse = self.rma_id.in_warehouse_id
        if not warehouse:
            if not operation.in_warehouse_id or not operation.out_warehouse_id:
                warehouse = self.env["stock.warehouse"].search(
                    [
                        ("company_id", "=", self.rma_id.company_id.id),
                        ("lot_rma_id", "!=", False),
                    ],
                    limit=1,
                )
                if not warehouse:
                    raise ValidationError(
                        _("Please define a warehouse with a " "default rma location.")
                    )
        location = self.rma_id.location_id
        if not location:
            location = (
                operation.location_id
                or operation.in_warehouse_id.lot_rma_id
                or warehouse.lot_rma_id
            )
        data = {
            "partner_id": self.partner_id.id,
            "description": self.rma_id.description,
            "sale_line_id": line.id,
            "product_id": product.id,
            "lot_id": lot and lot.id or False,
            "origin": line.order_id.name,
            "uom_id": uom_id or product.uom_id.id,
            "operation_id": operation.id,
            "product_qty": quantity,
            "delivery_address_id": self.sale_id.partner_shipping_id.id,
            "invoice_address_id": self.sale_id.partner_invoice_id.id,
            "price_unit": line.product_id == product
            and line.currency_id._convert(
                line.price_unit,
                line.currency_id,
                line.company_id,
                line.order_id.date_order,
            )
            or product.lst_price,
            "rma_id": self.rma_id.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "receipt_policy": operation.receipt_policy,
            "location_id": location.id,
            "refund_policy": operation.refund_policy,
            "delivery_policy": operation.delivery_policy,
            "in_warehouse_id": warehouse.id or operation.in_warehouse_id.id,
            "out_warehouse_id": warehouse.id or operation.out_warehouse_id.id,
        }
        return data

    @api.model
    def _get_rma_data(self):
        data = {"date_rma": fields.Datetime.now()}
        return data

    @api.model
    def _get_existing_sale_lines(self):
        existing_sale_lines = []
        for rma_line in self.rma_id.rma_line_ids:
            existing_sale_lines.append(rma_line.sale_line_id)
        return existing_sale_lines

    def _should_create_rma_line(self, line, existing_sale_line, lot=False):
        if not lot and line in existing_sale_line:
            return False
        if lot and (
            lot.id not in self.lot_ids.ids
            or lot.id in self.rma_id.rma_line_ids.mapped("lot_id").ids
        ):
            return False
        return True

    def _create_from_move_line(self, line):
        return True

    def _get_lot_quantity_from_move_lines(self, sale_line):
        outgoing_lines = self.env["stock.move.line"]
        incoming_lines = self.env["stock.move.line"]
        sent_moves = sale_line.move_ids.filtered(
            lambda m: m.state == "done" and not m.scrapped
        )
        for move in sent_moves:
            if move.location_dest_id.usage == "customer" and (
                not move.origin_returned_move_id
                or (move.origin_returned_move_id and move.to_refund)
            ):
                outgoing_lines |= move.move_line_ids
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_lines |= move.move_line_ids
        sent_product_data = {}
        for line in outgoing_lines:
            key = (line.product_id, line.product_uom_id, line.lot_id)
            if key not in sent_product_data:
                sent_product_data[key] = 0.0
            sent_product_data[key] += line.quantity
        for line in incoming_lines:
            key = (line.product_id, line.product_uom_id, line.lot_id)
            if key not in sent_product_data:
                sent_product_data[key] = 0.0
            sent_product_data[key] -= line.quantity
        return sent_product_data

    def add_lines(self):
        rma_line_obj = self.env["rma.order.line"]
        existing_sale_line = self._get_existing_sale_lines()
        for line in self.sale_line_ids:
            if self._create_from_move_line(line):
                sent_produt_data = self._get_lot_quantity_from_move_lines(line)
                for (product, uom, lot), qty in sent_produt_data.items():
                    if not self._should_create_rma_line(
                        line, existing_sale_line, lot=lot
                    ):
                        continue
                    data = self._prepare_rma_line_from_sale_order_line(
                        line, product, qty, uom_id=uom.id, lot=lot
                    )
                    rec = rma_line_obj.create(data)
                    # Ensure that configuration on the operation is applied
                    # TODO MIG: in v16 the usage of such onchange can be removed in
                    #  favor of (pre)computed stored editable fields for all policies
                    #  and configuration in the RMA operation.
                    rec._onchange_operation_id()
            else:
                if not self._should_create_rma_line(line, existing_sale_line):
                    continue
                # we can't have lot management based on sale order line
                data = self._prepare_rma_line_from_sale_order_line(
                    line,
                    line.product_id,
                    line.product_uom_qty,
                    uom_id=line.product_uom.id,
                    lot=False,
                )
                rec = rma_line_obj.create(data)
                # Ensure that configuration on the operation is applied
                # TODO MIG: in v16 the usage of such onchange can be removed in
                #  favor of (pre)computed stored editable fields for all policies
                #  and configuration in the RMA operation.
                rec._onchange_operation_id()
                rec.price_unit = rec._get_price_unit()
        rma = self.rma_id
        data_rma = self._get_rma_data()
        rma.write(data_rma)
        return {"type": "ir.actions.act_window_close"}
