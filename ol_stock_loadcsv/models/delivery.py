# Import Odoo libs
from odoo import fields, models


class DeliveryCarrierMapping(models.Model):
    """
    Create a mapping from v8 to v10 delivery carriers for use by the csv upload
    """

    _inherit = "delivery.carrier"

    # COLUMNS #####
    v10_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier", string="V10 Version"
    )
    # END #########
