from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'delivery.carrier'
    _inherit = ['delivery.carrier', 'res.uuid']

    ts_api_enabled = fields.Boolean(
        string='Enabled in Tax & Shipping API',
        help=(
            "Controls if the carrier is enabled in the Tax & Shipping API. Normal delivery address based"
            " filtering will still be applied "
        ),
        default=False,
    )

    ts_api_country_ids = fields.Many2many(
        'res.country', 'delivery_carrier_country_ts_api_rel', 'carrier_id', 'country_id', 'Countries'
    )
    ts_api_state_ids = fields.Many2many(
        'res.country.state', 'delivery_carrier_state_ts_api_rel', 'carrier_id', 'state_id', 'States'
    )
    ts_api_zip_from = fields.Char('Zip From')
    ts_api_zip_to = fields.Char('Zip To')
    ts_api_zip_list = fields.Char(string="Zip Ranges", help="Formatted like this: (123-456,567-789)")

    def ts_api_available_carriers(self, sale_order):
        """
        Filter carriers based on the Tax & Shipping carrier settings
        This mimics the core `available_carriers` method
        """
        carriers = self.filtered(
            lambda c: c.ts_api_enabled
            and c._ts_api_match_address(sale_order.partner_shipping_id)
            and c._ts_api_free_over(sale_order)
        )
        return carriers

    def _ts_api_free_over(self, sale_order):
        """
        Apply the `Free Over` logic to the Tax & Shipping API
        """
        if self.free_over and sale_order._compute_amount_total_without_delivery() < self.amount:
            return False
        return True

    def _ts_api_match_address(self, partner):
        """
        Match the address based on the Tax & Shipping carrier settings
        This mimics the core `_match_address` method
        """
        self.ensure_one()

        if self.zip_list:

            multi_zip_address_result = self._match_multi_zip_address(
                partner,
                country_ids=self.ts_api_country_ids,
                state_ids=self.ts_api_state_ids,
                zip_list=self.ts_api_zip_list,
            )

            if self.delivery_type == 'multi_zip':
                # If this carrier is of type `multi_zip`
                # we want to return the result of the multi_zip match
                return multi_zip_address_result

            if not multi_zip_address_result:
                # If this carrier is not of type `multi_zip`
                # but has a `zip_list` set, we only return if the multi_zip match failed
                # This means that if the multi_zip match succeeded we still apply the core address validation
                return False

        if self.ts_api_country_ids and partner.country_id not in self.ts_api_country_ids:
            return False
        if self.ts_api_state_ids and partner.state_id not in self.ts_api_state_ids:
            return False
        if self.ts_api_zip_from and (partner.zip or '').upper() < self.ts_api_zip_from.upper():
            return False
        if self.ts_api_zip_to and (partner.zip or '').upper() > self.ts_api_zip_to.upper():
            return False
        return True
