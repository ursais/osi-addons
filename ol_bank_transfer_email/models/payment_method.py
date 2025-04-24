# Import Odoo libs
from odoo import api, fields, models


class PaymentMethod(models.Model):
    """Add new field to Payment Method."""

    _inherit = "payment.method"

    # COLUMNS #####

    sale_email_template_id = fields.Many2one(
        "mail.template",
        help="""When set, if this payment method is set on the sale quotation,"""
        """it will send the email during confirmation of the sale order.""",
    )
    # END #########
    