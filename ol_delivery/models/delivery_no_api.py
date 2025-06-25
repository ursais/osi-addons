from odoo import models, fields, _

import logging

_logger = logging.getLogger(__name__)


class ProviderNoApi(models.Model):
    _inherit = "delivery.carrier"

    ### COLUMNS #######
    delivery_type = fields.Selection(
        selection_add=[("no_api", "No API")],
        ondelete={"no_api": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})},
    )

    ### END COLUMNS ###

    def no_api_rate_shipment(self, order):
        """
        Simply return 0.0 as price
        """

        return {"success": True, "price": 0.0, "error_message": False, "warning_message": False}
