# Copyright 2016 ForgeFlow S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, models


class RmaLineMakeSupplierRma(models.TransientModel):
    _inherit = "rma.order.line.make.supplier.rma"

    @api.model
    def _prepare_supplier_rma_line(self, rma, item):
        res = super()._prepare_supplier_rma_line(rma, item)
        if res["operation_id"]:
            operation = self.env["rma.operation"].browse(res["operation_id"])
            res["refund_policy"] = operation.refund_policy
        return res
