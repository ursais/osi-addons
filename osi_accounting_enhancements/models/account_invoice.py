# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    supplier_invoice_number = fields.Char(
        string="Supplier Invoice Number",
        help="The reference of this invoice as provided by the supplier.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    _sql_constraints = [
        (
            "supplier_invoice_number_uniq",
            "unique(supplier_invoice_number,partner_id)",
            "Supplier Invoice Number must be unique per Supplier!",
        )
    ]

    @api.multi
    def copy(self, default=None):
        default = dict(
            default or {},
            name=_("%s (copy)") % self.name,
            supplier_invoice_number=False,
        )
        return super(AccountInvoice, self).copy(default=default)

    @api.model
    def _prepare_refund(
        self, invoice, date_invoice=None, date=None, description=None, journal_id=None
    ):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice,
            date_invoice=date_invoice,
            date=date,
            description=description,
            journal_id=journal_id,
        )
        for field in ["supplier_invoice_number", "date_due"]:
            if field == "supplier_invoice_number":
                if invoice[field]:
                    values[field] = "Refund-{}-{}".format(description, invoice[field])
                else:
                    values[field] = "Refund-{}-{}".format(description, self.number)
            else:
                values[field] = invoice[field] or False
        return values

    # Commented By MG:05/21/2020 -- Don't want Supplier Invoice unique/mandatory
    # @api.multi
    # def invoice_validate(self):
    #
    #     res = super(AccountInvoice, self).invoice_validate()
    #     for invoice in self:
    #
    #         if invoice.type in ['out_refund','out_invoice']:
    #             continue
    #
    #         if not invoice.supplier_invoice_number:
    #             raise Warning(_('Please Enter Supplier Invoice Number!'))
    #
    #         inv_ids = self.search([
    #             ('supplier_invoice_number',
    #              '=', invoice.supplier_invoice_number),
    #             ('partner_id', '=', invoice.partner_id.id)])
    #         if len(inv_ids) > 1:
    #             raise Warning(_('Please Enter Unique Supplier Invoice Number '
    #                             'per Supplier!'))
    #     return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        for line in res:
            if line.get("invl_id", False):
                invl = self.env["account.invoice.line"].browse(
                    line.get("invl_id", False)
                )
                line["purchase_id"] = invl.purchase_order_id.id
                line["purchase_ref"] = invl.purchase_order_id.name

        return res

    @api.model
    def line_get_convert(self, line, part):

        res = super(AccountInvoice, self).line_get_convert(line, part)

        purchase_id = line.get("purchase_id", False)
        purchase_ref = line.get("purchase_ref", False)

        if not purchase_id:
            inv_id = line.get("invoice_id", False)
            invoice_line_ids = (
                self.env["account.invoice"].browse(inv_id).invoice_line_ids
            )

            purchase_id = False
            purchase_ref = False

            for invl in invoice_line_ids:

                if invl.purchase_order_id.id:
                    if not purchase_ref or not (
                        purchase_ref != invl.purchase_order_id.name
                    ):
                        purchase_ref = invl.purchase_order_id.name
                        purchase_id = invl.purchase_order_id.id
                    else:
                        purchase_ref = "Multiple"
                        purchase_id = False
                        break

        res["purchase_id"] = purchase_id
        res["purchase_ref"] = purchase_ref

        return res

    @api.multi
    def action_move_create(self):
        # for inv in self:
        #    if not inv.date_invoice:
        #        raise Warning(_('Please Enter Invoice Date!'))
        res = super(AccountInvoice, self).action_move_create()

        # Write invoice date in move and move lines
        for inv in self:
            for line in inv.move_id.line_ids:
                line.write(
                    {
                        "invoice_id": inv.id,
                        "supplier_invoice_number": inv.supplier_invoice_number or "",
                    }
                )
        return res

    @api.onchange("payment_term_id", "date_invoice")
    def _onchange_payment_term_date_invoice(self):
        date_invoice = self.date_invoice
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        if not self.payment_term_id:
            # When no payment term defined
            self.date_due = self.date_due or self.date_invoice
        else:
            pterm = self.payment_term_id
            pterm_list = pterm.with_context(
                currency_id=self.company_id.currency_id.id
            ).compute(value=1, date_ref=date_invoice)[0]
            if pterm_list:
                self.date_due = max(line[0] for line in pterm_list)
            else:
                raise ValidationError(
                    _("Insufficient Data!"),
                    _(
                        "The payment term of supplier does not have a payment "
                        "term line."
                    ),
                )

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        data["purchase_order_id"] = line.order_id.id
        return data


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    purchase_order_id = fields.Many2one(
        "purchase.order", string="Purchase Order Id", copy=False
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    supplier_invoice_number = fields.Char(
        string="Supplier Invoice Number",
        readonly=True,
        help="The reference of this invoice as provided by the supplier.",
    )
    purchase_id = fields.Many2one(
        "purchase.order", string="Purchase Order", readonly=True
    )
    purchase_ref = fields.Char(string="Purchase Reference", readonly=True)
    invoice_type = fields.Selection(
        related="invoice_id.type", string="Invoice Type", store=True
    )

    @api.multi
    def open_reconcile_view(self):
        res = super(AccountMoveLine, self).open_reconcile_view()
        ids = []
        is_purchase = False
        for aml in self:
            if aml.invoice_id and aml.invoice_id.type in ["in_refund", "in_invoice"]:
                is_purchase = True
            if aml.account_id.reconcile:
                ids.extend(
                    [r.debit_move_id.id for r in aml.matched_debit_ids]
                    if aml.credit > 0
                    else [r.credit_move_id.id for r in aml.matched_credit_ids]
                )
                ids.append(aml.id)
        if is_purchase:
            [action] = self.env.ref(
                "osi_accounting_enhancements" ".action_account_moves_all_a_purchase"
            ).read()
            action["domain"] = [("id", "in", ids)]
            return action
        return res
