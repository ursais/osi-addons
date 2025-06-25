import logging
import odoo.api

_logger = logging.getLogger(__name__)


def set_shipping_buffer_values_to_match_magento(cr):
    # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    # Populated from Magento config
    magento_values = {
        # US Company
        1: {
            "305b2df2-1569-4fd8-aaa6-d173a72cf515": 6,  # Free Shipping
            "5937178d-e55e-4e05-8695-ac249cb9bb17": 0,  # UPS Next Day Air
            "cd3aabac-5d77-48a2-ad1d-7210e491ce3c": 0,  # UPS Second Day Air
            "170858e6-6a84-4250-93a5-c58b22ea0589": 0,  # UPS Ground
            "c9440572-42c6-4210-8080-81fafe939acd": 0,  # UPS Worldwide Express
            "2d4334b9-e746-4a79-89e0-e6487fab9d23": 0,  # UPS Worldwide Expedited
            "bf25a5a0-8a61-4a2e-9364-3cafccef4125": 1,  # Economy
        },
        # EU Company
        2: {
            "305b2df2-1569-4fd8-aaa6-d173a72cf515": 1,  # Free Shipping
            "b52448c9-dce7-443c-9de9-f9bac4a47816": 1,  # UPS Standard
            "93abc17b-936c-416b-9c89-7f3385f20a7f": 1,  # UPS Saver
        },
    }

    # Find each delivery carrier and update the shipping buffer to match magento
    for company, values in magento_values.items():
        for carrier, value in values.items():
            query = f"""
                SELECT id
                FROM delivery_carrier
                WHERE uuid = %(uuid)s
            """
            query_args = {'uuid': carrier}
            env.cr.execute(query, query_args)
            record_ids = [x[0] for x in env.cr.fetchall()]
            shipping_method = env['delivery.carrier'].browse(record_ids)
            shipping_method.with_context(force_company=company).shipping_buffer = value


def migrate(cr, installed_version):
    _logger.info(f'Start Migration post script for: ls_tax_and_shipping_api v1.1')
    set_shipping_buffer_values_to_match_magento(cr)
    _logger.info(f'End Migration post script for: ls_tax_and_shipping_api v1.1')
