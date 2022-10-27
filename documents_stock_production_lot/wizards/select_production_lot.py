# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class SelectProdctionLot(models.TransientModel):
    _name = "select.production.lot"
    _description = "Select existing Lot/Tracking Number"

    lot_id = fields.Many2one(
        "stock.production.lot",
        string="Lot/Tracking Number",
    )

    def action_select_lot_number(self):
        ctx = self._context
        if ctx.get("documents"):
            documents = self.env["documents.document"].browse(ctx["documents"])
            for document in documents:
                # this_document is the document in use for the workflow
                this_document = document
                if (
                    document.res_model or document.res_id
                ) and document.res_model != "documents.document":
                    attachment_copy = document.attachment_id.with_context(
                        no_document=True
                    ).copy()
                    this_document = document.copy({"attachment_id": attachment_copy.id})
                this_document.write(
                    {
                        "res_model": self.lot_id._name,
                        "res_id": self.lot_id.id,
                    }
                )
            view_id = self.env.ref("stock.view_production_lot_form").id
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.production.lot",
                "name": "Lot/Tracking Number",
                "context": ctx,
                "view_mode": "form",
                "views": [(view_id, "form")],
                "res_id": self.lot_id.id,
                "view_id": view_id,
                "target": "current",
            }
