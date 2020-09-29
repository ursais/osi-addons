# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    supplier_invoice_number = fields.Char(
        "Supplier Invoice Number",
        readonly=True,
        help="The reference of this invoice as provided by the supplier.",
    )
    purchase_ref = fields.Char("Purchase Reference", readonly=True)

    @api.multi
    def voucher_move_line_create(
        self, line_total, move_id, company_currency, current_currency
    ):
        """
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        """
        for line in self.line_ids:
            # create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(line.price_unit * line.quantity)
            move_line = {
                "journal_id": self.journal_id.id,
                "name": line.name or "/",
                "account_id": line.account_id.id,
                "move_id": move_id,
                "partner_id": self.partner_id.id,
                "analytic_account_id": line.account_analytic_id
                and line.account_analytic_id.id
                or False,
                "quantity": 1,
                "credit": abs(amount) if self.voucher_type == "sale" else 0.0,
                "debit": abs(amount) if self.voucher_type == "purchase" else 0.0,
                "date": self.account_date,
                "tax_ids": [(4, t.id) for t in line.tax_ids],
                "amount_currency": line.price_subtotal
                if current_currency != company_currency
                else 0.0,
                "currency_id": company_currency != current_currency
                and current_currency
                or False,
                "supplier_invoice_number": line.invoice_id
                and line.invoice_id.supplier_invoice_number
                or "",
                "purchase_ref": line.purchase_ref or "",
            }

            self.env["account.move.line"].with_context(apply_taxes=True).create(
                move_line
            )
        return line_total


class AccountVoucherLine(models.Model):
    _inherit = "account.voucher.line"

    supplier_invoice_number = fields.Char(string="Sup.Inv.#")
    purchase_ref = fields.Char(string="PO Ref.#")
    invoice_id = fields.Many2one(
        "account.invoice", "Invoice ID", copy=False, readonly=True
    )

    def create(self, vals):
        if vals.get("move_line_id"):
            aml = self.env["account.move.line"].browse(vals.get("move_line_id"))
            sin_num = aml.name
            po_ref = aml.purchase_ref
            if sin_num:
                vals.update({"supplier_invoice_number": sin_num})
            if po_ref:
                vals.update({"purchase_ref": po_ref})
        return super(AccountVoucherLine, self).create(vals)
