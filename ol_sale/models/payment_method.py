# Import Odoo libs
from odoo import fields, models


class PaymentMethod(models.Model):
    """Add new field to Payment Method."""

    _inherit = "payment.method"

    # COLUMNS #####

    allow_quote_payment = fields.Boolean(string="Allow Payments on Sent Quotes")

    # END #########
