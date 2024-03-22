# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import ValidationError


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    def _prepare_payment_vals(self, invoices):
        res = super()._prepare_payment_vals(invoices)
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
