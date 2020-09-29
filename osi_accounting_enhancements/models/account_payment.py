# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    supplier_invoice_number = fields.Char(
        "Supplier Invoice Number",
        readonly=True,
        help="The reference of this invoice as provided by the supplier.",
    )
    purchase_ref = fields.Char("Purchase Reference", readonly=True)

    def _get_shared_move_line_vals(
        self, debit, credit, amount_currency, move_id, invoice_id=False
    ):
        """ Returns values common to both move lines (except for debit,
            credit and amount_currency which are reversed)
        """
        rec = super()._get_shared_move_line_vals(
            debit=debit,
            credit=credit,
            amount_currency=amount_currency,
            move_id=move_id,
            invoice_id=invoice_id,
        )
        if (
            self._context
            and self._context.get("default_payment_type", False)
            and self._context.get("default_payment_type") == "transfer"
        ):
            return rec

        if not invoice_id and self._context.get("active_model") != "hr.expense.sheet":
            invoice_id = self.env["account.invoice"].browse(
                self._context.get("active_ids")
            )

        id = invoice_id and invoice_id.id or False
        sin = False
        pref = False

        # Payment registered against multiple invoices using
        # more->register payment option
        if (
            invoice_id
            and len(invoice_id) == 1
            and invoice_id.type in ("in_invoice", "in_refund")
        ):

            purchase_ref = False
            for line in invoice_id.move_id.line_ids:
                if line.account_id.internal_type == "payable":
                    purchase_ref = line.purchase_ref

            id = invoice_id.id
            sin = invoice_id.supplier_invoice_number
            pref = purchase_ref

        rec.update(
            {"invoice_id": id, "supplier_invoice_number": sin, "purchase_ref": pref}
        )
        return rec
