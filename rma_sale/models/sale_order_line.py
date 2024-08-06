# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models
from odoo.osv import expression


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _rec_names_search = ["name", "order_id"]

    @api.model
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

    def _get_sale_line_rma_name_get_label(self):
        self.ensure_one()
        return "SO:{} | INV: {}, | PART:{} | QTY:{}".format(
            self.order_id.name,
            " ".join(str(x) for x in [inv.name for inv in self.order_id.invoice_ids]),
            self.product_id.name,
            self.product_uom_qty,
        )

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for sale_line in self:
            for sale_line in self:
                if sale_line.order_id.name:
                    sale_line.display_name = (
                        sale_line._get_sale_line_rma_name_get_label()
                    )
                else:
                    return super(SaleOrderLine, sale_line)._compute_display_name()

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA", ondelete="restrict", copy=False
    )

    def _prepare_order_line_procurement(self, group_id=False):
        vals = super()._prepare_order_line_procurement(group_id=group_id)
        vals.update({"rma_line_id": self.rma_line_id.id})
        return vals
