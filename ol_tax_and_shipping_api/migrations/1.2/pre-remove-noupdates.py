import logging
import odoo.api

_logger = logging.getLogger(__name__)


def remove_delivery_carrier_xml_noupdate(cr):
    # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    # Copy back the old data
    query = """
            UPDATE
                ir_model_data imd
            SET
                noupdate = NULL
            WHERE
                (
                    ("module" = 'delivery'
                    AND "name" = 'free_delivery_carrier'
                    )
                OR
                    "module" IN ('delivery_ups', 'delivery_usps', 'ls_delivery', 'ls_delivery_ups', 'ls_delivery_custom', 'ls_tax_and_shipping_api')
                )
                AND model = 'delivery.carrier'
                """
    env.cr.execute(query)

    # Disable the redundant EU Warehouse pickup
    warehouse_dc = env['delivery.carrier'].browse(189)
    warehouse_dc.write({'name': f"[DEPRECATED] {warehouse_dc.name}", 'active': False})


def migrate(cr, installed_version):
    _logger.info(f'Start Migration pre script for: ls_tax_and_shipping_api v1.2')
    remove_delivery_carrier_xml_noupdate(cr)
    _logger.info(f'End Migration pre script for: ls_tax_and_shipping_api v1.2')
