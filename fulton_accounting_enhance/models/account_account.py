# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import ValidationError
import re

ACCOUNT_CODE_REGEX = re.compile(r'^[A-Za-z0-9.\-]+$')

class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.constrains('code')
    def _check_account_code(self):
        for account in self:
            if not re.match(ACCOUNT_CODE_REGEX, account.code):
                raise ValidationError(_(
                    "The account code can only contain alphanumeric characters and dots."
                ))
