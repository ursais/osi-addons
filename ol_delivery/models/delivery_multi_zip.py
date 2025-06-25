from odoo import models, fields, _

import logging

_logger = logging.getLogger(__name__)


class ProviderMultiZip(models.Model):
    _inherit = "delivery.carrier"

    ### COLUMNS #######
    delivery_type = fields.Selection(
        selection_add=[("multi_zip", "Multi Zip")],
        ondelete={"multi_zip": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})},
    )
    zip_list = fields.Char(string="Zip Ranges", help="Formatted like this: (123-456,567-789)")

    ### END COLUMNS ###

    def multi_zip_rate_shipment(self, order):
        """
        Simply return 0.0 as price
        """

        return {"success": True, "price": 0.0, "error_message": False, "warning_message": False}

    def _match_address(self, partner):
        """
        Change the address filtering for Multi Zip carrier
        """
        self.ensure_one()

        if self.zip_list:

            multi_zip_address_result = self._match_multi_zip_address(partner)

            if self.delivery_type == "multi_zip":
                # If this carrier is of type `multi_zip`
                # we want to return the result of the multi_zip match
                return multi_zip_address_result

            if not multi_zip_address_result:
                # If this carrier is not of type `multi_zip`
                # but has a `zip_list` set, we only return if the multi_zip match failed
                # This means that if the multi_zip match succeeded we still apply the core address validation
                return False

        return super()._match_address(partner)

    def _match_multi_zip_address(self, partner, country_ids=None, state_ids=None, zip_list=None):
        """
        filtering for Multi Zip carrier
        """

        # Allow overrides
        country_ids = country_ids or self.country_ids
        state_ids = state_ids or self.state_ids
        zip_list = zip_list or self.zip_list

        # Keep some of the core validation
        if country_ids and partner.country_id not in country_ids:
            return False
        if state_ids and partner.state_id not in state_ids:
            return False

        # Validate based on the multi zip logic
        partner_zip = partner.zip
        zip_range = zip_list.split(",")
        
        if not partner_zip:
            # If the partner has no zip code, we can't validate
            return False

        for zip in zip_range:
            low, high = zip.split("-")
            if low < partner_zip and partner_zip < high:
                return True

        return False
