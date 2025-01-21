# Copyright (C) 2024, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _generate_nacha_batch_trailer_record(self):
        entry = []
        amount = self._get_total_cents(self.payment_ids)
        entry.append("7460")
        entry.append("{:06d}".format(len(self.payment_ids)))
        entry.append("{:010d}".format(0))
        entry.append("{:20.20}".format(""))
        entry.append("{:012d}".format(amount))
        entry.append("{:28.28}".format(""))
        return "".join(entry)

    def _generate_nacha_trailer(self):
        entry = []
        entry.append("9")
        entry.append("{:06d}".format(1))
        entry.append("{:06d}".format(len(self.payment_ids)))
        entry.append("{:67.67}".format(""))
        return "".join(entry)

    def _generate_nacha_entry_detail(self, payment_nr, payment, is_offset):
        if self.journal_id.nacha_file_type == "80_byte":
            amount = sum(payment.mapped("amount"))
            amount = self._get_total_cents(payment)
            entry = []
            if len(payment) > 1:
                payment = payment[0]
            self._validate_bank_for_nacha(payment)

            reference = "{}{:011d}".format("CK", payment.id)
            entry.append("6C")
            entry.append("{:1.1}".format(""))
            entry.append(
                "{:4.4}".format(str(payment.partner_bank_id.bank_id.bic or ""))
            )
            entry.append("{:<5.5}".format(payment.partner_bank_id.aba_routing))
            entry.append("{:<12.12}".format(payment.partner_bank_id.acc_number))
            entry.append("{:5.5}".format(""))

            entry.append("{:010d}".format(amount))
            entry.append("{:<13.13}".format(reference))
            entry.append(
                "{}{:<21.21}".format(" ", payment.partner_bank_id.acc_holder_name)
            )
            entry.append("{:6.6}".format(""))
            return "".join(entry)
        else:
            return super()._generate_nacha_entry_detail(payment_nr, payment, is_offset)

    def _generate_nacha_batch_header_record(self, date, batch_nr):
        if self.journal_id.nacha_file_type == "80_byte":
            batch = []
            batch.append("5")
            batch.append("{:46.46}".format(""))
            batch.append("{:3.3}".format("460"))
            batch.append("{:10.10}".format(""))
            batch.append("{:6.6}".format(self.date.strftime("%y%m%d")))
            batch.append("{:14.14}".format(""))
            return "".join(batch)
        else:
            return super()._generate_nacha_batch_header_record(date, batch_nr)

    def _generate_nacha_header(self):
        if self.journal_id.nacha_file_type == "80_byte":
            # Ensure all mandatory fields are filled
            if not self.journal_id.nacha_immediate_destination:
                raise ValidationError(
                    _("Destination Data Center (Immediate Destination) is not filled.")
                )
            if not self.journal_id.nacha_immediate_origin:
                raise ValidationError(
                    _("Originator Number (Immediate Origin) is not filled.")
                )
            if not self.journal_id.bank_account_id.bank_id.bic:
                raise ValidationError(_("Institution Number (BIC) is not filled."))
            if not self.journal_id.bank_account_id.aba_routing:
                raise ValidationError(
                    _("Branch Transit Number (ABA Routing) is not filled.")
                )
            if not self.journal_id.bank_account_id.acc_number:
                raise ValidationError(_("Account Number is not filled."))
            if not self.journal_id.nacha_company_identification:
                raise ValidationError(_("Originator's Short Name is not filled."))
            if not self.currency_id.name:
                raise ValidationError(_("Currency Indicator is not filled."))

            # Prepare fields for the header
            sequence = self.env["ir.sequence"].next_by_code("nacha.file.sequence")
            if sequence == "10000":
                sequence = "0001"
                sequence_id = self.env.ref(
                    "osi_nacha_80_byte.ir_sequence_file_number",
                )
                sequence_id.number_next_actual = 2
            destination = "{:>5.5}".format(self.journal_id.nacha_immediate_destination)
            space1 = "{:>5.5}".format("")
            origin = "{:>10.10}".format(self.journal_id.nacha_immediate_origin)
            now_in_client_tz = fields.Datetime.context_timestamp(
                self, fields.Datetime.now()
            )
            file_creation_date = "{:6.6}".format(
                now_in_client_tz.strftime("%y%m%d")
            )  # File Creation Date
            file_creation_number = str(sequence).zfill(4)
            institution_number = "{:>4.4}".format(
                self.journal_id.bank_account_id.bank_id.bic
            )
            branch_transit_number = "{:>5.5}".format(
                self.journal_id.bank_account_id.aba_routing
            )
            account_number = self.journal_id.bank_account_id.acc_number.ljust(11)
            space2 = "{:>2.2}".format("")
            originator_name = self.journal_id.nacha_company_identification.ljust(15)
            currency_indicator = self.currency_id.name.ljust(3)
            space3 = "{:>4.4}".format("")

            # Combine fields into an 80-character file header
            header = (
                "1  "
                + destination
                + space1
                + origin
                + file_creation_date
                + file_creation_number
                + " "
                + institution_number
                + branch_transit_number
                + account_number
                + space2
                + originator_name
                + " "
                + currency_indicator
                + space3
            ).ljust(80)
            return header
        else:
            return super()._generate_nacha_header()

    def _generate_nacha_file(self):
        if self.journal_id.nacha_file_type == "80_byte":
            entries = []
            header = self._generate_nacha_header()
            batch_nr = 0

            entries.append(
                self._generate_nacha_batch_header_record(self.date, batch_nr)
            )
            for date, payments in sorted(
                self.payment_ids.grouped("partner_bank_id").items()
            ):
                entries.append(
                    self._generate_nacha_entry_detail(0, payments, is_offset=False)
                )
            entries.append(self._generate_nacha_batch_trailer_record())
            entries.append(self._generate_nacha_trailer())
            return "\r\n".join([header] + entries)
        else:
            return super()._generate_nacha_file()
