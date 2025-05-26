# Import Odoo libs
from odoo import fields, models


class PaymentPreference(models.Model):
    _name = 'res.paypref'
    _description = 'Payment Preference'
    _order="name"

    # COLUMNS #####

    name = fields.Char(string="Payment Preference (short name)", required=True)

    # END #########
