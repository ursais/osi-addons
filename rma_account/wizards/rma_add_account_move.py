# Copyright 2017 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaAddAccountMove(models.TransientModel):
    _name = "rma_add_account_move"
    _description = "Wizard to add rma lines"

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
        res["line_ids"] = False
        return res

    rma_id = fields.Many2one(
        "rma.order", string="RMA Order", readonly=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", readonly=True
    )
    line_ids = fields.Many2many(
        "account.move.line",
        "rma_add_account_move_add_line_rel",
        "account_move_line_id",
        "rma_add_move_id",
        string="Invoice Lines",
    )

    def _prepare_rma_line_from_inv_line(self, line):
        if self.env.context.get("customer"):
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
                    _("Please define a warehouse with a" " default rma location")
                )
        data = {
            "partner_id": self.partner_id.id,
            "account_move_line_id": line.id,
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
            "rma_id": self.rma_id.id,
            "receipt_policy": operation.receipt_policy,
            "refund_policy": operation.refund_policy,
            "delivery_policy": operation.delivery_policy,
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

    @api.model
    def _get_rma_data(self):
        data = {"date_rma": fields.Datetime.now()}
        return data

    @api.model
    def _get_existing_invoice_lines(self):
        existing_invoice_lines = []
        for rma_line in self.rma_id.rma_line_ids:
            existing_invoice_lines.append(rma_line.account_move_line_id)
        return existing_invoice_lines

    def add_lines(self):
        rma_line_obj = self.env["rma.order.line"]
        existing_invoice_lines = self._get_existing_invoice_lines()
        for line in self.line_ids.filtered(lambda aml: aml.display_type == "product"):
            # Load a PO line only once
            if line not in existing_invoice_lines:
                data = self._prepare_rma_line_from_inv_line(line)
                rec = rma_line_obj.create(data)
                # Ensure that configuration on the operation is applied (like
                #  policies).
                # TODO MIG: in v16 the usage of such onchange can be removed in
                #  favor of (pre)computed stored editable fields for all policies
                #  and configuration in the RMA operation.
                rec._onchange_operation_id()
        rma = self.rma_id
        data_rma = self._get_rma_data()
        rma.write(data_rma)
        return {"type": "ir.actions.act_window_close"}
