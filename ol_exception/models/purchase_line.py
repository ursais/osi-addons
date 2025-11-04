# Import Odoo libs
import html
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """
    Inherit PO Line/Exception adding fields similar to parent order.
    These are needed in order for the email template functionality which
    don't exist in the original OCA modules.
    """

    _inherit = ["purchase.order.line", "base.exception.method"]
    _name = "purchase.order.line"

    # COLUMNS ######

    exception_ids = fields.Many2many(
        "exception.rule",
        string="Exceptions",
        copy=False,
        readonly=True,
    )
    exceptions_summary = fields.Html(
        readonly=True,
        compute="_compute_exceptions_summary",
    )
    is_exception_danger = fields.Boolean(compute="_compute_is_exception_danger")

    # END ##########
    # METHODS ######

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

    # END ##########
