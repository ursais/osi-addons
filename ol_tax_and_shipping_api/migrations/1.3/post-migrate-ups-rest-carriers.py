import logging
import uuid as uuid_lib
import odoo.api

_logger = logging.getLogger(__name__)


def remove_delivery_carrier_xml_noupdate(cr):
    # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    ups_carriers = env['delivery.carrier'].search([("delivery_type", "=", "ups_rest")])
    
    for carrier in ups_carriers:
        carrier.write(
            {
                "ts_api_enabled": carrier.ups_legacy_carrier_id.ts_api_enabled,
                "ts_api_country_ids": [(6, 0, carrier.ups_legacy_carrier_id.ts_api_country_ids.ids)],
                "ts_api_state_ids": [(6, 0, carrier.ups_legacy_carrier_id.ts_api_state_ids.ids)],
                "ts_api_zip_from": carrier.ups_legacy_carrier_id.ts_api_zip_from,
                "ts_api_zip_to": carrier.ups_legacy_carrier_id.ts_api_zip_to,
                "ts_api_zip_list": carrier.ups_legacy_carrier_id.ts_api_zip_list,
                "uuid": uuid_lib.uuid4(),
            }
        )
        _logger.info(f"Updated `{carrier.name}({carrier.id})` with Tax & Shipping Data`")


def migrate(cr, installed_version):
    _logger.info(f'Start Migration post script for: ls_tax_and_shipping_api v1.3')
    remove_delivery_carrier_xml_noupdate(cr)
    _logger.info(f'End Migration post script for: ls_tax_and_shipping_api v1.3')
