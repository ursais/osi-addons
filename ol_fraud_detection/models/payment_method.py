# Import Odoo libs
from odoo import fields, models


class aymentMethod(models.Model):
    """Inherit payment method to add fraud check setting field."""

    _inherit = "payment.method"

    # COLUMNS #####

    check_risk = fields.Boolean("Check Maxmind Risk")

    # END #########
