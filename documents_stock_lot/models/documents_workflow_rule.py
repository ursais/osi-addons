# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class DocumentsWorkflowRule(models.Model):
    _inherit = ["documents.workflow.rule"]

    def _compute_business(self):
        return self._get_business()

    has_business_option = fields.Boolean(default=True, compute="_compute_business")
    create_model = fields.Selection(
        selection_add=[("stock.lot", "Lot/Tracking Number")]
    )

    def create_record(self, documents=None):
        res = super().create_record(documents=documents)
        if self.create_model == "stock.lot":
            ctx = self._context.copy()
            ctx.update({"documents": documents.ids})
            view_id = self.env.ref("documents_stock_lot.select_lot_view_form").id
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.lot",
                "name": "Lot/Tracking Number",
                "context": ctx,
                "view_mode": "form",
                "target": "new",
                "views": [(view_id, "form")],
                "view_id": view_id,
            }
        return res
