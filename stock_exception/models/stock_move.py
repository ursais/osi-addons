# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import html
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = ["stock.move", "base.exception.method"]
    _name = "stock.move"

    exception_ids = fields.Many2many(
        "exception.rule", string="Exceptions", copy=False, readonly=True
    )
    exceptions_summary = fields.Html(
        readonly=True, compute="_compute_exceptions_summary"
    )
    ignore_exception = fields.Boolean(
        related="picking_id.ignore_exception", store=True, string="Ignore Exceptions"
    )
    is_exception_danger = fields.Boolean(compute="_compute_is_exception_danger")

    @api.depends("exception_ids", "ignore_exception")
    def _compute_is_exception_danger(self):
        for rec in self:
            rec.is_exception_danger = (
                len(rec.exception_ids) > 0 and not rec.ignore_exception
            )

    @api.depends("exception_ids", "ignore_exception")
    def _compute_exceptions_summary(self):
        for rec in self:
            if rec.exception_ids and not rec.ignore_exception:
                rec.exceptions_summary = rec._get_exception_summary()
            else:
                rec.exceptions_summary = False

    def _get_exception_summary(self):
        return "<ul>%s</ul>" % "".join(
            [
                f"<li>{html.escape(e.name)}: <i>{html.escape(e.description)}</i></li>"
                for e in self.exception_ids
            ]
        )

    def _get_main_records(self):
        return self.mapped("picking_id")

    @api.model
    def _reverse_field(self):
        return "picking_ids"

    def _detect_exceptions(self, rule):
        records = super()._detect_exceptions(rule)
        return records.mapped("picking_id")
