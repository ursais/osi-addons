# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("line_ids.rma_line_ids")
    def _compute_used_in_rma_count(self):
        for inv in self:
            rmas = inv.mapped("line_ids.rma_line_ids")
            inv.used_in_rma_count = len(rmas)

    @api.depends("line_ids.rma_line_id")
    def _compute_rma_count(self):
        for inv in self:
            rmas = inv.mapped("line_ids.rma_line_id")
            inv.rma_count = len(rmas)

    def _prepare_invoice_line_from_rma_line(self, rma_line):
        sequence = max(self.line_ids.mapped("sequence")) + 1 if self.line_ids else 10
        qty = rma_line.qty_to_refund
        if float_compare(qty, 0.0, precision_rounding=rma_line.uom_id.rounding) <= 0:
            qty = 0.0
        data = {
            "move_id": self.id,
            "product_uom_id": rma_line.uom_id.id,
            "product_id": rma_line.product_id.id,
            "price_unit": rma_line.company_id.currency_id._convert(
                rma_line._get_price_unit(),
                self.currency_id,
                self.company_id,
                self.date,
                round=False,
            ),
            "quantity": qty,
            "discount": 0.0,
            "rma_line_id": rma_line.id,
            "sequence": sequence + 1,
        }
        return data

    def _post_process_invoice_line_from_rma_line(self, new_line, rma_line):
        new_line.rma_line_id = rma_line
        new_line.name = f"{self.add_rma_line_id.name}: {new_line.name}"
        new_line.account_id = new_line.account_id
        return True

    @api.onchange("add_rma_line_id")
    def onchange_add_rma_line_id(self):
        if not self.add_rma_line_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_rma_line_id.partner_id.id

        new_line = self.env["account.move.line"]
        if self.add_rma_line_id not in (self.line_ids.mapped("rma_line_id")):
            data = self._prepare_invoice_line_from_rma_line(self.add_rma_line_id)
            new_line = new_line.new(data)
            self._post_process_invoice_line_from_rma_line(
                new_line, self.add_rma_line_id
            )
        # Compute invoice_origin.
        origins = set(self.line_ids.mapped("rma_line_id.name"))
        self.invoice_origin = ",".join(list(origins))
        self.add_rma_line_id = False

    rma_count = fields.Integer(compute="_compute_rma_count", string="# of RMA")
    used_in_rma_count = fields.Integer(
        compute="_compute_used_in_rma_count", string="# of Used in RMA"
    )

    add_rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="Add from RMA line",
        ondelete="set null",
        help="Create a refund in based on an existing rma_line",
    )

    def action_view_used_in_rma(self):
        rmas = self.mapped("line_ids.rma_line_ids")
        return self._prepare_action_view_rma(rmas)

    def action_view_rma(self):
        rmas = self.mapped("line_ids.rma_line_id")
        return self._prepare_action_view_rma(rmas)

    def _prepare_action_view_rma(self, rmas):
        if self.move_type in ["in_invoice", "in_refund"]:
            action = self.env.ref("rma.action_rma_supplier_lines")
            form_view = self.env.ref("rma.view_rma_line_supplier_form", False)
        else:
            action = self.env.ref("rma.action_rma_customer_lines")
            form_view = self.env.ref("rma.view_rma_line_form", False)
        result = action.sudo().read()[0]
        rma_ids = rmas.ids
        # choose the view_mode accordingly
        if not rma_ids:
            result["domain"] = [("id", "in", [])]
        elif len(rma_ids) > 1:
            result["domain"] = [("id", "in", rma_ids)]
        else:
            res = form_view
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = rma_ids and rma_ids[0] or False
        return result

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        product_model = self.env["product.product"]
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for line in res:
            if line.get("product_id", False):
                product = product_model.browse(line.get("product_id", False))
                if (
                    line.get("account_id")
                    != product.categ_id.property_stock_valuation_account_id.id
                ):
                    current_move = self.browse(line.get("move_id", False))
                    current_rma = current_move.invoice_line_ids.filtered(
                        lambda x, product=product: x.rma_line_id
                        and x.product_id.id == product.id
                    ).mapped("rma_line_id")
                    if len(current_rma) == 1:
                        line.update({"rma_line_id": current_rma.id})
                    elif len(current_rma) > 1:
                        find_with_label_rma = current_rma.filtered(
                            lambda x, line=line: x.name == line.get("name")
                        )
                        if len(find_with_label_rma) == 1:
                            line.update({"rma_line_id": find_with_label_rma.id})
        return res

    def _stock_account_get_last_step_stock_moves(self):
        rslt = super()._stock_account_get_last_step_stock_moves()
        for invoice in self.filtered(lambda x: x.move_type == "out_invoice"):
            rslt += invoice.mapped("line_ids.rma_line_id.move_ids").filtered(
                lambda x: x.state == "done" and x.location_dest_id.usage == "customer"
            )
        for invoice in self.filtered(lambda x: x.move_type == "out_refund"):
            # Add refunds generated from the RMA
            rslt += invoice.mapped("line_ids.rma_line_id.move_ids").filtered(
                lambda x: x.state == "done" and x.location_id.usage == "customer"
            )
        return rslt
