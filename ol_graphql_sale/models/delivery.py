# Import Python libs

# Import Odoo libs
from odoo import fields, models


class DeliveryCarrier(models.Model):
    """
    Add decoding/encoding for delivery methods
    """

    _inherit = "delivery.carrier"

    # COLUMNS #####

    # These two fields identify and link the shipping method from the e-commerce site and the delivery method in Odoo
    message_carrier = fields.Char(
        string="Carrier shorthand",
        help="The carrier shorthand of the delivery method we receive from the e-commerce platform",
        required=False,
    )

    message_code = fields.Char(
        string="Carrier code",
        help="The carrier code of the delivery method we receive from the e-commerce platform",
        required=False,
    )
    # END #########

    _sql_constraints = [
        (
            "uniq_message_code_and_carrier",
            "UNIQUE(company_id, message_code, message_carrier)",
            "Cannot have the same code and carrier for multiple delivery methods in the same company",
        )
    ]
