# Copyright (C) 2019, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from odoo.tools.float_utils import float_compare

try:
    from num2words import num2words
except ImportError:
    logging.getLogger(__name__).warning(
        "The num2words python library is not\
     installed."
    )
    num2words = None

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    "out_invoice": "customer",
    "out_refund": "customer",
    "in_invoice": "supplier",
    "in_refund": "supplier",
}

# Since invoice amounts are unsigned,
# this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    "out_invoice": 1,
    "in_refund": 1,
    "in_invoice": -1,
    "out_refund": -1,
}


class InvoiceCustomerPaymentLine(models.TransientModel):
    _name = "invoice.customer.payment.line"
    _description = "Invoice Customer Payment Line"
    _rec_name = "invoice_id"

    def _get_payment_difference(self):
        for rec in self:
            rec.payment_difference = rec.balance_amt - rec.receiving_amt

    invoice_id = fields.Many2one(
        "account.invoice", string="Customer Invoice", required=True
    )
    partner_id = fields.Many2one("res.partner", string="Customer Name", required=True)
    balance_amt = fields.Float("Invoice Balance", required=True)
    wizard_id = fields.Many2one("account.register.payments", string="Wizard")
    receiving_amt = fields.Float("Receive Amount", required=True)
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_method_id = fields.Many2one("account.payment.method", string="Payment Type")
    payment_difference = fields.Float(
        compute="_get_payment_difference", string="Difference Amount"
    )
    payment_difference_handling = fields.Selection(
        [("open", "Keep open"), ("reconcile", "Mark invoice as fully paid")],
        default="open",
        string="Action",
        copy=False,
    )
    writeoff_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "!=", True)],
        copy=False,
    )
    reason_code = fields.Many2one("payment.adjustment.reason", string="Reason Code")
    note = fields.Text("Note")

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        """
            Raise warning while the invoice is changed.
        """
        raise ValidationError(_("Invoice is unchangeable!"))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
            Raise warning while the Customer is changed.
        """
        raise ValidationError(_("Customer is unchangeable!"))

    @api.onchange("balance_amt")
    def _onchange_balance_amt(self):
        """
            Raise warning while the Balance Amount is changed.
        """
        raise ValidationError(_("Balance is unchangeable!"))

    @api.onchange("receiving_amt")
    def _onchange_amount(self):
        check_amount_in_words = num2words(
            math.floor(self.receiving_amt), lang="en"
        ).title()
        decimals = self.receiving_amt % 1
        if decimals >= 10 ** -2:
            check_amount_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )
        self.check_amount_in_words = check_amount_in_words
        self.payment_difference = self.balance_amt - self.receiving_amt


class InvoicePaymentLine(models.TransientModel):
    _name = "invoice.payment.line"
    _description = "Invoice Payment Line"
    _rec_name = "invoice_id"

    def _get_payment_difference(self):
        for rec in self:
            rec.payment_difference = rec.balance_amt - rec.paying_amt

    invoice_id = fields.Many2one(
        "account.invoice", string="Supplier Invoice", required=True
    )
    partner_id = fields.Many2one("res.partner", string="Supplier Name", required=True)
    balance_amt = fields.Float("Balance Amount", required=True)
    wizard_id = fields.Many2one("account.register.payments", string="Wizard")
    paying_amt = fields.Float("Pay Amount", required=True)
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_difference = fields.Float(
        compute="_get_payment_difference", string="Difference Amount", readonly=True
    )
    payment_difference_handling = fields.Selection(
        [("open", "Keep open"), ("reconcile", "Mark invoice as fully paid")],
        default="open",
        string="Action",
        copy=False,
    )
    writeoff_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "!=", True)],
        copy=False,
    )
    reason_code = fields.Many2one("payment.adjustment.reason", string="Reason Code")
    note = fields.Text("Note")

    @api.onchange("paying_amt")
    def _onchange_amount(self):
        check_amount_in_words = num2words(
            math.floor(self.paying_amt), lang="en"
        ).title()
        decimals = self.paying_amt % 1
        if decimals >= 10 ** -2:
            check_amount_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )
        self.check_amount_in_words = check_amount_in_words
        self.payment_difference = self.balance_amt - self.paying_amt

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        """
            Raise warning while the invoice is changed.
        """
        raise ValidationError(_("Invoice is unchangeable!"))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
            Raise warning while the Customer is changed.
        """
        raise ValidationError(_("Customer is unchangeable!"))

    @api.onchange("balance_amt")
    def _onchange_balance_amt(self):
        """
            Raise warning while the Balance Amount is changed.
        """
        raise ValidationError(_("Balance is unchangeable!"))


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    @api.multi
    @api.depends("invoice_customer_payments.receiving_amt")
    def _compute_customer_pay_total(self):
        self.total_customer_pay_amount = sum(
            line.receiving_amt for line in self.invoice_customer_payments
        )

    @api.multi
    @api.depends("invoice_payments.paying_amt")
    def _compute_pay_total(self):
        self.total_pay_amount = sum(line.paying_amt for line in self.invoice_payments)

    is_auto_fill = fields.Char(string="Auto-Fill Pay Amount")
    invoice_payments = fields.One2many(
        "invoice.payment.line", "wizard_id", string="Payments"
    )
    is_customer = fields.Boolean(string="Is Customer?")
    invoice_customer_payments = fields.One2many(
        "invoice.customer.payment.line", "wizard_id", string="Receipts"
    )
    cheque_amount = fields.Float("Batch Payment Total", required=True)
    total_pay_amount = fields.Float("Invoices Total:", compute="_compute_pay_total")
    total_customer_pay_amount = fields.Float(
        "Total Invoices:", compute="_compute_customer_pay_total"
    )

    @api.model
    def default_get(self, fields):
        if self.env.context and not self.env.context.get("batch", False):
            return super(AccountRegisterPayments, self).default_get(fields)

        context = dict(self._context or {})
        active_model = context.get("active_model")
        active_ids = context.get("active_ids")
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _(
                    "Program error: wizard action executed without\
             active_model or active_ids in context."
                )
            )
        if active_model != "account.invoice":
            raise UserError(
                _(
                    "Program error: the expected model for this\
             action is 'account.invoice'. The provided one is '%d'."
                )
                % active_model
            )
        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != "open" for invoice in invoices):
            raise UserError(
                _(
                    "You can only register payments for \
            open invoices"
                )
            )
        if any(
            MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
            != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
            for inv in invoices
        ):
            raise UserError(
                _(
                    "You cannot mix customer invoices and vendor\
             bills in a single payment."
                )
            )
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(
                _(
                    "In order to pay multiple invoices at once,\
             they must use the same currency."
                )
            )
        rec = {}
        if "batch" in context and context.get("batch"):
            payment_lines = []
            if MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] == "customer":
                for inv in invoices:
                    payment_lines.append(
                        (
                            0,
                            0,
                            {
                                "partner_id": inv.partner_id.id,
                                "invoice_id": inv.id,
                                "balance_amt": inv.residual or 0.0,
                                "receiving_amt": 0.0,
                                "payment_difference": inv.residual or 0.0,
                                "payment_difference_handling": "open",
                            },
                        )
                    )
                rec.update(
                    {"invoice_customer_payments": payment_lines, "is_customer": True}
                )
            else:
                for inv in invoices:
                    payment_lines.append(
                        (
                            0,
                            0,
                            {
                                "partner_id": inv.partner_id.id,
                                "invoice_id": inv.id,
                                "balance_amt": inv.residual or 0.0,
                                "paying_amt": 0.0,
                            },
                        )
                    )
                rec.update({"invoice_payments": payment_lines, "is_customer": False})
        else:
            # Checks on received invoice records
            if any(
                MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
                != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
                for inv in invoices
            ):
                raise UserError(
                    _(
                        "You cannot mix customer invoices and\
                 vendor bills in a single payment."
                    )
                )

        total_amount = sum(
            inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices
        )
        rec.update(
            {
                "amount": abs(total_amount),
                "currency_id": invoices[0].currency_id.id,
                "payment_type": total_amount > 0 and "inbound" or "outbound",
                "partner_id": invoices[0].commercial_partner_id.id,
                "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            }
        )
        return rec

    def get_payment_batch_vals(self, inv_payment=False, group_data={}):
        if group_data:
            res = {
                "journal_id": self.journal_id.id,
                "payment_method_id": "payment_method_id" in group_data
                and group_data["payment_method_id"]
                or self.payment_method_id.id,
                "payment_date": self.payment_date,
                "communication": group_data["memo"],
                "invoice_ids": [
                    (4, int(inv), None) for inv in list(group_data["inv_val"])
                ],
                "payment_type": self.payment_type,
                "amount": group_data["total"],
                "currency_id": self.currency_id.id,
                "partner_id": int(group_data["partner_id"]),
                "partner_type": group_data["partner_type"],
            }
            if self.payment_method_id == self.env.ref(
                "account_check_printing.account_payment_method_check"
            ):
                res.update(
                    {
                        "check_amount_in_words": group_data[
                            "total_check_amount_in_words"
                        ]
                        or ""
                    }
                )
            return res

    @api.multi
    def make_payments(self):
        # Make group data either for Customers or Vendors
        context = dict(self._context or {})
        group_data = {}
        memo = self.communication or " "
        if self.is_customer:
            context.update({"is_customer": True})
            if (
                float_compare(self.total_customer_pay_amount, self.cheque_amount, 2)
                != 0
            ):
                raise ValidationError(
                    _(
                        "Verification Failed! Total Invoices\
                 Amount and Check amount does not match!."
                    )
                )
            for data_get in self.invoice_customer_payments:
                if data_get.receiving_amt > 0:
                    data_get.payment_difference = (
                        data_get.balance_amt - data_get.receiving_amt
                    )
                    partner_id = str(data_get.invoice_id.partner_id.id)
                    if partner_id in group_data:
                        old_total = group_data[partner_id]["total"]
                        # build memo value
                        if memo:
                            memo = (
                                group_data[partner_id]["memo"]
                                + " : "
                                + memo
                                + "-"
                                + str(data_get.invoice_id.number)
                            )
                        else:
                            memo = (
                                group_data[partner_id]["memo"]
                                + " : "
                                + str(data_get.invoice_id.number)
                            )
                        # calculate amount in words
                        total_check_amount_in_words = num2words(
                            math.floor(old_total + data_get.receiving_amt)
                        ).title()
                        decimals = (old_total + data_get.receiving_amt) % 1
                        if decimals >= 10 ** -2:
                            total_check_amount_in_words += _(" and %s/100") % str(
                                int(
                                    round(
                                        float_round(
                                            decimals * 100, precision_rounding=1
                                        )
                                    )
                                )
                            )
                        # prepare name
                        name = ""
                        if data_get.reason_code:
                            name = str(data_get.reason_code.code)
                        if data_get.note:
                            name = name + ": " + str(data_get.note)
                        if not name:
                            name = "Counterpart"
                        group_data[partner_id].update(
                            {
                                "partner_id": partner_id,
                                "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                                    data_get.invoice_id.type
                                ],
                                "total": old_total + data_get.receiving_amt,
                                "memo": memo,
                                "temp_invoice": data_get.invoice_id.id,
                                "payment_method_id": data_get.payment_method_id
                                and data_get.payment_method_id.id
                                or False,
                                "total_check_amount_in_words": total_check_amount_in_words,
                            }
                        )
                        group_data[partner_id]["inv_val"].update(
                            {
                                str(data_get.invoice_id.id): {
                                    "line_name": name,
                                    "receiving_amt": data_get.receiving_amt,
                                    "payment_difference_handling": data_get.payment_difference_handling,
                                    "payment_difference": data_get.payment_difference,
                                    "writeoff_account_id": data_get.writeoff_account_id
                                    and data_get.writeoff_account_id.id
                                    or False,
                                }
                            }
                        )
                    else:
                        # build memo value
                        if self.communication:
                            memo = (
                                self.communication
                                + "-"
                                + str(data_get.invoice_id.number)
                            )
                        else:
                            memo = str(data_get.invoice_id.number)
                        # calculate amount in words
                        total_check_amount_in_words = num2words(
                            math.floor(math.floor(data_get.receiving_amt))
                        ).title()
                        decimals = data_get.receiving_amt % 1
                        if decimals >= 10 ** -2:
                            total_check_amount_in_words += _(" and %s/100") % str(
                                int(
                                    round(
                                        float_round(
                                            decimals * 100, precision_rounding=1
                                        )
                                    )
                                )
                            )
                        # prepare name
                        name = ""
                        if data_get.reason_code:
                            name = str(data_get.reason_code.code)
                        if data_get.note:
                            name = name + ": " + str(data_get.note)
                        if not name:
                            name = "Counterpart"
                        group_data.update(
                            {
                                partner_id: {
                                    "partner_id": partner_id,
                                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                                        data_get.invoice_id.type
                                    ],
                                    "total": data_get.receiving_amt,
                                    "payment_method_id": data_get.payment_method_id
                                    and data_get.payment_method_id.id
                                    or False,
                                    "total_check_amount_in_words": total_check_amount_in_words,
                                    "memo": memo,
                                    "temp_invoice": data_get.invoice_id.id,
                                    "inv_val": {
                                        str(data_get.invoice_id.id): {
                                            "line_name": name,
                                            "receiving_amt": data_get.receiving_amt,
                                            "payment_difference_handling": data_get.payment_difference_handling,
                                            "payment_difference": data_get.payment_difference,
                                            "writeoff_account_id": data_get.writeoff_account_id
                                            and data_get.writeoff_account_id.id
                                            or False,
                                        }
                                    },
                                }
                            }
                        )
        else:
            context.update({"is_customer": False})
            if float_compare(self.total_pay_amount, self.cheque_amount, 2) != 0:
                raise ValidationError(
                    _(
                        "Verification Failed! Total Invoices\
                         Amount and Check amount does not match!."
                    )
                )
            for data_get in self.invoice_payments:
                if data_get.paying_amt > 0:
                    # Get difference amt
                    data_get.payment_difference = (
                        data_get.balance_amt - data_get.paying_amt
                    )
                    partner_id = str(data_get.invoice_id.partner_id.id)
                    if partner_id in group_data:
                        old_total = group_data[partner_id]["total"]
                        # build memo value
                        if self.communication:
                            memo = (
                                group_data[partner_id]["memo"]
                                + " : "
                                + self.communication
                                + "-"
                                + str(data_get.invoice_id.number)
                            )
                        else:
                            memo = (
                                group_data[partner_id]["memo"]
                                + " : "
                                + str(data_get.invoice_id.number)
                            )
                        #                        # calculate amount in words
                        total_check_amount_in_words = num2words(
                            math.floor(old_total + data_get.paying_amt)
                        ).title()
                        decimals = (old_total + data_get.paying_amt) % 1

                        if decimals >= 10 ** -2:
                            total_check_amount_in_words += _(" and %s/100") % str(
                                int(
                                    round(
                                        float_round(
                                            decimals * 100, precision_rounding=1
                                        )
                                    )
                                )
                            )
                        group_data[partner_id].update(
                            {
                                "partner_id": partner_id,
                                "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                                    data_get.invoice_id.type
                                ],
                                "total": old_total + data_get.paying_amt,
                                "memo": memo,
                                "temp_invoice": data_get.invoice_id.id,
                                "total_check_amount_in_words": total_check_amount_in_words,
                            }
                        )
                        # prepare name
                        name = ""
                        if data_get.reason_code:
                            name = str(data_get.reason_code.code)
                        if data_get.note:
                            name = name + ": " + str(data_get.note)
                        if not name:
                            name = "Counterpart"
                        # Update with payment diff data
                        group_data[partner_id]["inv_val"].update(
                            {
                                str(data_get.invoice_id.id): {
                                    "line_name": name,
                                    "paying_amt": data_get.paying_amt,
                                    "payment_difference_handling": data_get.payment_difference_handling,
                                    "payment_difference": data_get.payment_difference,
                                    "writeoff_account_id": data_get.writeoff_account_id
                                    and data_get.writeoff_account_id.id
                                    or False,
                                }
                            }
                        )
                    else:
                        # build memo value
                        if self.communication:
                            memo = (
                                self.communication
                                + "-"
                                + str(data_get.invoice_id.number)
                            )
                        else:
                            memo = str(data_get.invoice_id.number)
                        # calculate amount in words
                        total_check_amount_in_words = num2words(
                            math.floor(data_get.paying_amt)
                        ).title()
                        decimals = data_get.paying_amt % 1
                        # prepare name
                        name = ""
                        if data_get.reason_code:
                            name = str(data_get.reason_code.code)
                        if data_get.note:
                            name = name + ": " + str(data_get.note)
                        if not name:
                            name = "Counterpart"
                        if decimals >= 10 ** -2:
                            total_check_amount_in_words += _(" and %s/100") % str(
                                int(
                                    round(
                                        float_round(
                                            decimals * 100, precision_rounding=1
                                        )
                                    )
                                )
                            )
                        group_data.update(
                            {
                                partner_id: {
                                    "partner_id": partner_id,
                                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                                        data_get.invoice_id.type
                                    ],
                                    "total": data_get.paying_amt,
                                    "total_check_amount_in_words": total_check_amount_in_words,
                                    "memo": memo,
                                    "temp_invoice": data_get.invoice_id.id,
                                    "inv_val": {
                                        str(data_get.invoice_id.id): {
                                            "line_name": name,
                                            "paying_amt": data_get.paying_amt,
                                            "payment_difference_handling": data_get.payment_difference_handling,
                                            "payment_difference": data_get.payment_difference,
                                            "writeoff_account_id": data_get.writeoff_account_id
                                            and data_get.writeoff_account_id.id
                                            or False,
                                        }
                                    },
                                }
                            }
                        )
        # update context
        context.update({"group_data": group_data})
        # making partner wise payment
        payment_ids = []
        for p in list(group_data):
            # update active_ids with active invoice id
            if context.get("active_ids", False) and group_data[p].get(
                "temp_invoice", False
            ):
                context.update({"active_ids": group_data[p]["temp_invoice"]})
            payment = (
                self.env["account.payment"]
                .with_context(context)
                .create(self.get_payment_batch_vals(group_data=group_data[p]))
            )
            payment_ids.append(payment.id)
            payment.post()

        view_id = self.env["ir.model.data"].get_object_reference(
            "osi_payment_batch_process", "view_account_supplier_payment_tree_nocreate"
        )[1]
        return {
            "name": _("Payments"),
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "account.payment",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "new",
            "domain": "[('id','in',%s)]" % (payment_ids),
            "context": {"group_by": "partner_id"},
        }

    @api.multi
    def auto_fill_payments(self):
        ctx = self._context.copy()
        for wiz in self:
            if wiz.is_customer:
                if wiz.invoice_customer_payments:
                    for payline in wiz.invoice_customer_payments:
                        payline.write(
                            {
                                "receiving_amt": payline.balance_amt,
                                "payment_difference": 0.0,
                            }
                        )
                ctx.update(
                    {
                        "reference": wiz.communication or "",
                        "journal_id": wiz.journal_id.id,
                    }
                )
            else:
                if wiz.invoice_payments:
                    for payline in wiz.invoice_payments:
                        payline.write({"paying_amt": payline.balance_amt})
                ctx.update(
                    {
                        "reference": wiz.communication or "",
                        "journal_id": wiz.journal_id.id,
                    }
                )
        return {
            "name": _("Batch Payments"),
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_id": self.id,
            "res_model": "account.register.payments",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
            "context": ctx,
        }
