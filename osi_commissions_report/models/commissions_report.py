# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CommissionsReport(models.TransientModel):
    """
    Commissions Report Model
    Shows all invoices with their referrer/commission information.
    Similar to Sales Not Attributed Report but includes ALL invoices.
    """
    _name = "commissions.report"
    _description = "Commissions Report"
    _order = "invoice_date desc, name"

    name = fields.Char(string="Invoice Number", readonly=True)
    invoice_date = fields.Date(string="Invoice Date", readonly=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer/Vendor",
        readonly=True,
    )
    referrer_id = fields.Many2one(
        "res.partner",
        string="Referrer",
        readonly=True,
    )
    amount_total = fields.Monetary(
        string="Total Amount",
        readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
    )
    move_type = fields.Selection(
        [
            ("out_invoice", "Customer Invoice"),
            ("out_refund", "Customer Credit Note"),
            ("in_invoice", "Vendor Bill"),
            ("in_refund", "Vendor Credit Note"),
            ("entry", "Journal Entry"),
        ],
        string="Type",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        readonly=True,
    )

    @api.model
    def _get_report_data(self):
        """
        Get all invoices with their referrer information.
        Returns account.move records with referrer_id field populated.
        """
        invoices = self.env["account.move"].search([
            ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
        ])
        return invoices

    @api.model
    def generate_report(self):
        """
        Generate the commissions report by creating report records from all invoices.
        This method is called automatically when the report is accessed.
        """
        # Clear existing report records to ensure fresh data
        self.search([]).unlink()

        invoices = self._get_report_data()
        report_vals = []
        for invoice in invoices:
            referrer_id = False
            if hasattr(invoice, "referrer_id") and invoice.referrer_id:
                referrer_id = invoice.referrer_id.id

            report_vals.append({
                "name": invoice.name or "/",
                "invoice_date": invoice.invoice_date,
                "partner_id": invoice.partner_id.id if invoice.partner_id else False,
                "referrer_id": referrer_id,
                "amount_total": invoice.amount_total,
                "currency_id": invoice.currency_id.id if invoice.currency_id else False,
                "move_type": invoice.move_type,
                "state": invoice.state,
                "invoice_id": invoice.id,
            })

        if report_vals:
            self.create(report_vals)
        return True

    def action_open_invoice(self):
        """
        Open the related invoice from the report.
        """
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            "name": "Invoice",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def action_view_report(self):
        """
        Action method to generate and view the report.
        Called from the menu action.
        """
        self.generate_report()
        return {
            "name": "Commissions Report",
            "type": "ir.actions.act_window",
            "res_model": "commissions.report",
            "view_mode": "tree,form",
            "domain": [],
            "context": {"create": False},
            "target": "current",
        }
