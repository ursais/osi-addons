# Copyright 2019 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        compute="_compute_picking_type_id",
        required=True,
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("warehouse_id")
    def _compute_picking_type_id(self):
        companies = self.env.context.get("allowed_company_ids", []).copy()
        companies.append(False)
        for order in self:
            order.picking_type_id = (
                self.env["stock.picking.type"]
                .search(
                    [
                        ("code", "=", "stock_request_order"),
                        "|",
                        ("warehouse_id.company_id", "in", companies),
                        ("warehouse_id", "=", self.warehouse_id.id or False),
                    ],
                    limit=1,
                )
                .id
            )
