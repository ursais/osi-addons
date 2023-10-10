# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = ["account.payment"]

    is_hide_check = fields.Boolean("Hide Check Number?")
    is_visible_check = fields.Boolean(
        "Is Visible Check", help="Use for the visible or invisible check number."
    )
    is_readonly_check = fields.Boolean(
        "Is Readonly Check", help="Use for the readonly or editable check number."
    )
    void_reason = fields.Char(string="Void Reason")
    voided_count = fields.Integer(
        string="# Voids", compute="_compute_stat_buttons_voided_count"
    )
    can_be_voided = fields.Boolean(
        string="Can be Voided", compute="_compute_can_be_voided"
    )

    @api.model
    def _compute_stat_buttons_voided_count(self):
        for payment in self:
            res = self.env["payment.check.void"].search_count(
                [("payment_id", "=", payment.id)]
            )
            payment.voided_count = res or 0

    @api.model
    def _compute_can_be_voided(self):
        for payment in self:
            payment.can_be_voided = False
            if (
                payment.payment_method_id.payment_type == "outbound"
                and payment.state == "posted"
                and payment.payment_state != "reversed"
            ):
                if (
                    payment.payment_method_code == "check_printing"
                    and payment.is_move_sent
                ):
                    payment.can_be_voided = True
                if payment.payment_method_code == "ACH-Out":
                    payment.can_be_voided = True
                if payment.payment_method_code == "manual" and payment.is_move_sent:
                    payment.can_be_voided = True

    @api.onchange("payment_method_id")
    def onchange_payment_method(self):
        """Allow to customer payment to enter check number.
        - Based on journal check printing manual True/False for vendor."""
        self.is_visible_check = False
        self.is_readonly_check = False
        if self.payment_method_id:
            if (
                self.payment_method_id.payment_type == "inbound"
                and self.payment_method_code in ("check_printing", "ACH-Out", "manual")
            ):
                self.is_visible_check = True
                self.check_number = 0
            elif self._context.get("is_vendor"):
                if (
                    self.payment_method_id.payment_type == "outbound"
                    and self.payment_method_code
                    in ("check_printing", "ACH-Out", "manual")
                ):
                    self.is_visible_check = False
            elif (
                self.payment_method_id.payment_type == "outbound"
                and self.payment_method_code in ("check_printing", "ACH-Out", "manual")
            ):
                self.is_visible_check = True
                if not self.check_manual_sequencing:
                    self.is_readonly_check = True

    def print_checks(self):
        for rec in self:
            if rec.payment_type == "outbound":
                domain = [
                    ("payment_id", "=", rec.id),
                    ("check_number", "=", int(rec.check_number)),
                ]
                payment_check_void_ids = self.env["payment.check.void"].search(
                    domain, order="id DESC", limit=1
                )
                is_manual = rec.journal_id.check_manual_sequencing
                if payment_check_void_ids and is_manual:
                    rec.check_number = rec.journal_id.check_next_number
                    rec.is_visible_check = True
                    sequence = rec.journal_id.check_sequence_id
                    sequence.next_by_id()
                    message = (
                        (
                            """<ul class="o_mail_thread_message_tracking">
                        <li>(_(Check Updated Date:)) %s</li>
                        <li>(_(Check Number:)) %s (Generated)</li>
                        <li>(_(State:)) %s</li></ul>"""
                        )
                        % (
                            fields.Date.to_string(fields.Datetime.now()),
                            rec.check_number,
                            rec.state.title(),
                        )
                    )
                    rec.message_post(body=message)
        result = super(AccountPayment, self).print_checks()
        return result

    def void_check_button(self):
        return {
            "name": _("Void Check"),
            "type": "ir.actions.act_window",
            "res_model": "simple.void.check",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_payment_id": self.id,
            },
        }

    def write(self, vals):
        if vals.get("check_number") and not str(vals.get("check_number")).isdigit():
            raise ValidationError(_("Check number must be integer."))
        result = super(AccountPayment, self).write(vals)
        check_hist_obj = self.env["payment.check.history"]
        for res in self:
            new_chk = False
            if "check_number" in vals and vals["check_number"] and res.check_number:
                check_hist = {
                    "name": res.name,
                    "payment_id": res.id,
                    "partner_id": res.partner_id.id,
                    "amount": res.amount,
                    "check_amount": res.amount,
                    "check_number": res.check_number,
                    "journal_id": res.journal_id.id,
                    "date": fields.Datetime.now(),
                    "create_date": fields.Datetime.now(),
                    "write_date": fields.Datetime.now(),
                    "create_uid": res.create_uid.id,
                    # "state": res.state,
                    "state": "sent",
                    "is_visible_check": not res.check_number,
                }
                new_chk = check_hist_obj.create(check_hist)
            check_ids = False
            if new_chk:
                check_ids = check_hist_obj.search(
                    [
                        ("payment_id", "=", res.id),
                        ("check_number", "=", res.check_number),
                        ("id", "!=", new_chk.id),
                    ],
                    limit=1,
                )
            # else:
            #     check_ids = check_hist_obj.search(
            #         [("payment_id", "=", res.id), ("write_date", "<=", res.write_date)],
            #         limit=1,
            #     )
            if check_ids:
                for chk in check_ids:
                    if res.state == "posted":
                        chk.write({"state": "sent"})
                    elif res.state == "draft":
                        chk.write({"state": "draft"})
                    elif res.state == "cancelled":
                        chk.write({"state": "cancelled"})
                    else:
                        chk.write({"state": "void"})
        return result

    def action_cancel(self):
        for rec in self:
            if rec.check_number and rec.payment_type == "outbound":
                raise ValidationError(
                    "You cannot cancel the payment because a check is already printed."
                )
            result = super(AccountPayment, rec).action_cancel()
            payment_check_history_obj = self.env["payment.check.history"]
            domain = [
                ("payment_id", "=", rec.id),
                ("partner_id", "=", rec.partner_id.id),
                ("journal_id", "=", rec.journal_id.id),
            ]
            if rec.check_number:
                domain += [("check_number", "=", rec.check_number)]
            payment_check_history_ids = payment_check_history_obj.search(
                domain, limit=1
            )
            payment_check_history_ids.write({"state": "cancelled"})

            # Set Messages....
            message = (
                """<ul class="o_mail_thread_message_tracking"><li>(_(Updated On:)) %s</li>
                <li>(_(Check Number:)) %s (Cancelled)</li>
                <li>(_(State:)) %s</li></ul>"""
                % (
                    fields.Date.to_string(fields.Datetime.now()),
                    rec.check_number,
                    rec.state,
                )
            )
            rec.message_post(body=message)
            rec.write({"is_hide_check": True})
        return result

    def void_check_reversal_payment(self):
        check_hist_obj = self.env["payment.check.history"]
        journal_id = self.journal_id and self.journal_id.id
        self._cr.execute(
            """
                SELECT DISTINCT(aml.move_id)
                FROM account_payment AS ap
                INNER JOIN account_move_line AS aml
                    ON aml.payment_id=ap.id
                    AND ap.id = %s
                INNER JOIN account_move AS am
                    ON aml.move_id = am.id
            """,
            (self.id,),
        )
        am_ids = self._cr.fetchone()
        if am_ids:
            am_ids = am_ids[0]

        for rec in self:
            # Update payment check history..
            check_ids = check_hist_obj.search(
                [("payment_id", "=", rec.id), ("check_number", "=", rec.check_number)],
                limit=1,
            )
            if check_ids:
                check_ids.write({"state": "posted"})
            self.write({"is_move_sent": False})
        return {
            "name": _("Reverse Moves"),
            "type": "ir.actions.act_window",
            "res_model": "account.move.reversal",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": {
                "is_void_button": True,
                "default_journal_id": journal_id or False,
                "account_move_id": am_ids,
                "payment_id": self.id,
            },
        }

    def button_void_checks(self):
        return {
            "name": _("Void Checks"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "payment.check.void",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("payment_id", "in", self.ids)],
        }

    def action_validate_invoice_payment(self):
        for record in self:
            if record.payment_type == "inbound" and record.payment_method_code in (
                "check_printing",
                "ACH-Out",
            ):
                if record.check_number <= 0:
                    raise ValidationError(_("Please Enter Check Number"))
        return super(AccountPayment, self).action_validate_invoice_payment()

    def post(self):
        res = super(AccountPayment, self).post()
        for record in self:
            if (
                record.payment_type == "inbound"
                and record.payment_method_code
                in ("check_printing", "ACH-Out", "manual")
                and not record.invoice_ids
                and record.check_number <= 0
            ):
                raise ValidationError(_("Please Enter Check Number"))
        return res


class PaymentCheckHistory(models.Model):
    _name = "payment.check.history"
    _description = "Payment Info for the check Payment Feature"
    _order = "id desc"

    name = fields.Char("Name", readonly=True)
    payment_id = fields.Many2one(
        "account.payment", string="Payment Info", readonly=True
    )
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    amount = fields.Float("Gross Amount", readonly=True)
    check_number = fields.Integer("Check Number", readonly=True)
    check_amount = fields.Float("Check Amount", readonly=True)
    journal_id = fields.Many2one("account.journal", "Journal", readonly=True)
    date = fields.Date(string="Date", readonly=True)
    create_date = fields.Datetime(string="Create Date", readonly=True)
    write_date = fields.Datetime(string="Write Date", readonly=True)
    create_uid = fields.Many2one(
        comodel_name="res.users", string="Created By", readonly=True
    )
    write_uid = fields.Many2one(
        comodel_name="res.users", string="Updated By", readonly=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("sent", "Sent"),
            ("void", "Void"),
            ("cancelled", "Cancelled"),
            ("reconciled", "Reconciled"),
        ],
        readonly=True,
        default="draft",
        copy=False,
        string="Status",
        tracking=True,
    )
    currency_id = fields.Many2one(
        related="payment_id.currency_id", string="Currency", readonly=True, store=True
    )
    is_visible_check = fields.Boolean(
        "Is Visible Check", help="Use for the visible or invisible check number."
    )

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)


class PaymentCheckVoid(models.Model):
    _name = "payment.check.void"
    _description = "Payment Check Void"
    _order = "check_number"

    bill_ref = fields.Char("Bill Number")
    create_date = fields.Date("Check Void Date")
    check_number = fields.Integer("Check Number")
    state = fields.Selection([("void", "Void")], string="State", default="void")
    payment_id = fields.Many2one("account.payment", "Payment")
    void_reason = fields.Char(string="Void Reason")


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    def _prepare_payment_vals(self, invoices):
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices)
        if (
            self.multi
            and self.payment_type == "inbound"
            and self.payment_method_code in ("check_printing", "ACH-Out", "manual")
            and self.check_number
        ):
            raise ValidationError(
                _(
                    "In order to receive multiple invoices\
                    payment from same check number, you must use the same\
                    Partner."
                )
            )
        if (
            self.payment_type == "inbound"
            and self.payment_method_code in ("check_printing", "ACH-Out", "manual")
            and self.check_number <= 0
        ):
            raise ValidationError(_("Please Enter Check Number"))
        else:
            if self.payment_type == "inbound" and self.payment_method_code in (
                "check_printing",
                "ACH-Out",
            ):
                res.update(
                    {
                        "check_number": self.check_number,
                        "is_visible_check": True if self.check_number > 0 else False,
                    }
                )
        return res
