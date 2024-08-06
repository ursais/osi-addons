# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_invoice_refund_count(self):
        for rec in self:
            invoices = rec.mapped("rma_line_ids.refund_line_ids.move_id")
            rec.invoice_refund_count = len(invoices)

    def _compute_invoice_count(self):
        for rec in self:
            invoices = rec.mapped("rma_line_ids.move_id")
            rec.invoice_count = len(invoices)

    add_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Add Invoice",
        ondelete="set null",
        readonly=True,
    )
    invoice_refund_count = fields.Integer(
        compute="_compute_invoice_refund_count", string="# of Refunds"
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count", string="# of Invoices"
    )

    def _prepare_rma_line_from_inv_line(self, line):
        if self.type == "customer":
            operation = (
                self.rma_line_ids.product_id.rma_customer_operation_id
                or self.rma_line_ids.product_id.categ_id.rma_customer_operation_id
            )
        else:
            operation = (
                self.rma_line_ids.product_id.rma_supplier_operation_id
                or self.rma_line_ids.product_id.categ_id.rma_supplier_operation_id
            )
        data = {
            "account_move_line_id": line.id,
            "product_id": line.product_id.id,
            "name": line.name,
            "origin": line.move_id.name,
            "uom_id": line.product_uom_id.id,
            "operation_id": operation,
            "product_qty": line.quantity,
            "price_unit": line.move_id.currency_id._convert(
                line.price_unit,
                line.currency_id,
                line.company_id,
                line.date,
                round=False,
            ),
            "rma_id": self.id,
        }
        return data

    @api.onchange("add_move_id")
    def onchange_invoice(self):
        if not self.add_move_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_move_id.partner_id.id
        new_lines = self.env["rma.order.line"]
        for line in self.add_move_id.line_ids:
            # Load a PO line only once
            if line in self.rma_line_ids.mapped("account_move_line_id"):
                continue
            data = self._prepare_rma_line_from_inv_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.rma_line_ids += new_lines
        self.date_rma = fields.Datetime.now()
        self.delivery_address_id = self.add_move_id.partner_id.id
        self.invoice_address_id = self.add_move_id.partner_id.id
        self.add_move_id = False
        return {}

    @api.model
    def prepare_rma_line(self, origin_rma, rma_id, line):
        line_values = super().prepare_rma_line(origin_rma, rma_id, line)
        line_values["invoice_address_id"] = line.invoice_address_id.id
        return line_values

    @api.model
    def _prepare_rma_data(self, partner, origin_rma):
        res = super()._prepare_rma_data(partner, origin_rma)
        res["invoice_address_id"] = partner.id
        return res

    def action_view_invoice_refund(self):
        move_ids = self.mapped("rma_line_ids.move_id").ids
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", move_ids)],
            "name": "Refunds",
            "res_model": "account.move",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }

    def action_view_invoice(self):
        move_ids = self.mapped("rma_line_ids.move_id").ids
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", move_ids)],
            "name": "Originating Invoice",
            "res_model": "account.move",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }
