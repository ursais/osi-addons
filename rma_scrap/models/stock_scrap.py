# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    rma_line_id = fields.Many2one("rma.order.line", string="RMA order Line")

    is_rma_scrap = fields.Boolean(
        string="Is RMA Scrap",
        default=False,
        copy=False,
        help="This Stock Move has been created from a Scrap operation in " "the RMA.",
    )

    def do_scrap(self):
        res = super().do_scrap()
        if self.is_rma_scrap:
            self.move_ids.is_rma_scrap = True
            self.rma_line_id.move_ids |= self.move_ids
        return res

    def _prepare_move_values(self):
        res = super()._prepare_move_values()
        res["rma_line_id"] = self.rma_line_id.id
        return res

    def action_view_rma_line(self):
        if self.rma_line_id.type == "customer":
            action = self.env.ref("rma.action_rma_customer_lines")
            res = self.env.ref("rma.view_rma_line_form", False)
        else:
            action = self.env.ref("rma.action_rma_supplier_lines")
            res = self.env.ref("rma.view_rma_line_supplier_form", False)
        result = action.sudo().read()[0]
        # choose the view_mode accordingly
        result["views"] = [(res and res.id or False, "form")]
        result["res_id"] = self.rma_line_id.id
        return result

    def action_validate(self):
        self.ensure_one()
        if float_is_zero(
            self.scrap_qty, precision_rounding=self.product_uom_id.rounding
        ):
            raise UserError(_("You can only enter positive quantities."))
        if self.product_id.type != "product":
            return self.do_scrap()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        available_qty = sum(
            self.env["stock.quant"]
            ._gather(
                self.product_id,
                self.location_id,
                self.lot_id,
                self.package_id,
                self.owner_id,
                strict=True,
            )
            .mapped("quantity")
        )
        scrap_qty = self.product_uom_id._compute_quantity(
            self.scrap_qty, self.product_id.uom_id
        )
        if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0:
            return self.do_scrap()
        else:
            ctx = dict(self.env.context)
            ctx.update(
                {
                    "default_product_id": self.product_id.id,
                    "default_location_id": self.location_id.id,
                    "default_scrap_id": self.id,
                    "default_quantity": scrap_qty,
                    "default_product_uom_name": self.product_id.uom_name,
                }
            )
            return {
                "name": self.product_id.display_name
                + _(": Insufficient Quantity To Scrap"),
                "view_mode": "form",
                "res_model": "stock.warn.insufficient.qty.scrap",
                "view_id": self.env.ref(
                    "stock.stock_warn_insufficient_qty_scrap_form_view"
                ).id,
                "type": "ir.actions.act_window",
                "context": ctx,
                "target": "new",
            }
