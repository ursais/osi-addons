from math import copysign

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


class AccountTax(models.Model):
    """Inherit to implement the tax using avatax API"""

    _inherit = "account.tax"

    @api.model
    def _get_avalara_tax_domain(self, tax_rate, doc_type):
        domain = super()._get_avalara_tax_domain(tax_rate, doc_type)
        # Ensure that the Tax calculation is percentage
        domain.append(("amount_type", "=", "percent"))
        return domain