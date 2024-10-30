# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.osv import expression


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _rec_names_search = ["name", "order_id"]

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="RMA",
    )

    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = domain or []
        if self.env.context.get("rma"):
            domain = expression.AND([domain, [("display_type", "=", False)]])
        lines = self.search([("order_id.name", operator, name)] + domain, limit=limit)
        if limit:
            limit_rest = limit - len(lines)
        else:
            # limit can be 0 or None representing infinite
            limit_rest = limit
        if limit_rest or not limit:
            domain += [("id", "in", lines.ids)]
            return super()._name_search(
                name, domain=domain, operator=operator, limit=limit_rest, order=order
            )
        return self._search(domain, limit=limit, order=order)

    def _get_purchase_line_rma_name_get_label(self):
        self.ensure_one()
        return "PO:{} | INV: {}, | PART:{} | QTY:{}".format(
            self.order_id.name,
            " ".join(str(x) for x in [inv.name for inv in self.order_id.invoice_ids]),
            self.product_id.name,
            self.product_uom_qty,
        )

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for purchase_line in self:
            for purchase_line in self:
                if purchase_line.order_id.name:
                    purchase_line.display_name = (
                        purchase_line._get_purchase_line_rma_name_get_label()
                    )
                else:
                    return super(
                        PurchaseOrderLine, purchase_line
                    )._compute_display_name()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            rma_line_id = self.env.context.get("rma_line_id")
            if rma_line_id:
                vals["rma_line_id"] = rma_line_id
        return super().create(vals_list)
