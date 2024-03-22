# Copyright (C) 2022, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import ValidationError

import base64
import math


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _generate_nacha_ccd_header(self):
        header = []
        header.append("1")  # Record Type Code
        header.append("01")  # Priority Code
        header.append(
            "{:>10.10}".format(self.journal_id.nacha_immediate_destination)
        )  # Immediate Destination
        header.append(
            "{:>10.10}".format(self.journal_id.nacha_immediate_origin)
        )  # Immediate Origin
        header.append(
            "{:6.6}".format(fields.Date.today().strftime("%y%m%d"))
        )  # File Creation Date

        now_in_client_tz = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()
        )
        header.append(
            "{:4.4}".format(now_in_client_tz.strftime("%H%M"))
        )  # File Creation Time

        nr = self.search_count([("id", "!=", self.id), ("date", "=", self.date)])
        header.append("{:1.1}".format(chr(min(90, ord("A") + nr))))  # File ID Modifier

        header.append("094")  # Record Size
        header.append("{:02d}".format(self._get_blocking_factor()))  # Blocking Factor
        header.append("1")  # Format Code
        header.append(
            "{:23.23}".format(self.journal_id.nacha_destination)
        )  # Destination
        header.append(
            "{:23.23}".format(self.journal_id.company_id.name)
        )  # Origin or Company Name

        # ideally this would be the display_name but it will be too long
        header.append("{:8d}".format(self.id))  # Reference Code

        return "".join(header)

    def _generate_nacha_ccd_batch_header_record(self, payment, batch_nr):
        batch = []
        batch.append("5")  # Record Type Code
        batch.append("220")  # Service Class Code (credits only)
        batch.append("{:16.16}".format(self.journal_id.company_id.name))  # Company Name
        batch.append("{:20.20}".format(""))  # Company Discretionary Data (optional)
        batch.append(
            "{:0>10.10}".format(self.journal_id.nacha_company_identification)
        )  # Company Identification
        batch.append("CCD")  # CCD Entry Class Code
        batch.append("{:10.10}".format(payment.ref))  # Company Entry Description
        batch.append(
            "{:6.6}".format(payment.date.strftime("%y%m%d"))
        )  # Company Descriptive Date
        batch.append(
            "{:6.6}".format(payment.date.strftime("%y%m%d"))
        )  # Effective Entry Date
        batch.append("{:3.3}".format(""))  # Settlement Date (Julian)
        batch.append("1")  # Originator Status Code
        batch.append(
            "{:8.8}".format(self.journal_id.nacha_origination_dfi_identification)
        )  # Originating DFI Identification
        batch.append("{:07d}".format(batch_nr))  # Batch Number

        return "".join(batch)

    def _generate_nacha_ccd_entry_detail(self, payment):
        bank = payment.partner_bank_id
        entry = []
        entry.append("6")  # Record Type Code (CCD)
        entry.append("22")  # Transaction Code
        entry.append(
            "{:8.8}".format(bank.aba_routing[:-1])
        )  # RDFI Routing Transit Number
        entry.append("{:1.1}".format(bank.aba_routing[-1]))  # Check Digit
        entry.append("{:17.17}".format(bank.acc_number))  # DFI Account Number
        entry.append("{:010d}".format(round(payment.amount * 100)))  # Amount
        entry.append(
            "{:15.15}".format(payment.partner_id.vat or "")
        )  # Individual Identification Number (optional)
        entry.append("{:22.22}".format(payment.partner_id.name))  # Individual Name
        entry.append("  ")  # Discretionary Data Field
        entry.append("0")  # Addenda Record Indicator

        # trace number
        entry.append(
            "{:8.8}".format(self.journal_id.nacha_origination_dfi_identification)
        )  # Trace Number (80-87)
        entry.append("{:07d}".format(0))  # Trace Number (88-94)

        return "".join(entry)

    def _calculate_aba_hash(self, aba_routing):
        # [:-1]: remove check digit
        # [-8:]: lower 8 digits
        return int(aba_routing[:-1][-8:])

    def _generate_nacha_ccd_batch_control_record(self, payment, batch_nr):
        bank = payment.partner_bank_id
        control = []
        control.append("8")  # Record Type Code
        control.append("220")  # Service Class Code (credits only)
        control.append("{:06d}".format(1))  # Entry/Addenda Count
        control.append(
            "{:010d}".format(self._calculate_aba_hash(bank.aba_routing))
        )  # Entry Hash
        control.append("{:012d}".format(0))  # Total Debit Entry Dollar Amount in Batch
        control.append(
            "{:012d}".format(round(payment.amount * 100))
        )  # Total Credit Entry Dollar Amount in Batch
        control.append(
            "{:0>10.10}".format(self.journal_id.nacha_company_identification)
        )  # Company Identification
        control.append(
            "{:19.19}".format("")
        )  # Message Authentication Code (leave blank)
        control.append("{:6.6}".format(""))  # Reserved (leave blank)
        control.append(
            "{:8.8}".format(self.journal_id.nacha_origination_dfi_identification)
        )  # Originating DFI Identification
        control.append("{:07d}".format(batch_nr))  # Batch Number

        return "".join(control)

    def _get_nr_of_records(self, payments):
        # File header
        # Per payment:
        #   - batch header
        #   - entry
        #   - batch control
        # File control record
        return 1 + len(payments) * 3 + 1

    def _generate_nacha_ccd_file_control_record(self, payments):
        control = []
        control.append("9")  # Record Type Code
        control.append("{:06d}".format(len(payments)))  # Batch Count

        # Records / Blocking Factor (always 10).
        # We ceil because we'll pad the file with 999's until a multiple of 10.
        block_count = math.ceil(
            self._get_nr_of_records(payments) / self._get_blocking_factor()
        )
        control.append("{:06d}".format(block_count))

        control.append("{:08d}".format(len(payments)))  # Entry/ Addenda Count

        hashes = sum(
            self._calculate_aba_hash(payment.partner_bank_id.aba_routing)
            for payment in payments
        )
        hashes = str(hashes)[-10:]  # take the rightmost 10 characters
        control.append("{:0>10}".format(hashes))  # Entry Hash

        control.append("{:012d}".format(0))  # Total Debit Entry Dollar Amount in File
        control.append(
            "{:012d}".format(sum(round(payment.amount * 100) for payment in payments))
        )  # Total Credit Entry Dollar Amount in File
        control.append("{:39.39}".format(""))  # Blank

        return "".join(control)

    def _generate_padding(self, payments):
        padding = []
        nr_of_records = self._get_nr_of_records(payments)

        while nr_of_records % 10:
            padding.append("9" * 94)
            nr_of_records += 1

        return padding

    def _generate_nacha_ccd_file(self):
        header = self._generate_nacha_ccd_header()
        entries = []
        for batch_nr, payment in enumerate(self.payment_ids):
            self._validate_payment_for_nacha(payment)
            self._validate_bank_for_nacha(payment)
            entries.append(
                self._generate_nacha_ccd_batch_header_record(payment, batch_nr)
            )
            entries.append(self._generate_nacha_ccd_entry_detail(payment))
            entries.append(
                self._generate_nacha_ccd_batch_control_record(payment, batch_nr)
            )

        entries.append(self._generate_nacha_ccd_file_control_record(self.payment_ids))
        entries.extend(self._generate_padding(self.payment_ids))

        return "\r\n".join([header] + entries)

    def _get_methods_generating_files(self):
        res = super(AccountBatchPayment, self)._get_methods_generating_files()
        res.append("nacha_ccd")
        return res

    def _generate_export_file(self):
        if self.payment_method_code == "nacha_ccd":
            self._validate_journal_for_nacha()
            data = self._generate_nacha_ccd_file()
            date = fields.Datetime.today().strftime("%m-%d-%Y")  # US date format
            return {
                "file": base64.encodebytes(data.encode()),
                "filename": "NACHA-CCD-%s-%s.txt" % (self.journal_id.code, date),
            }
        else:
            return super(AccountBatchPayment, self)._generate_export_file()
