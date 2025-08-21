# Import Odoo libs
from odoo import fields, models


class AccountPayment(models.Model):
    """Inherit Payment to add customer check number field."""

    _inherit = "account.payment"

    # COLUMNS #####

    customer_check_number = fields.Char()

    # END #########
