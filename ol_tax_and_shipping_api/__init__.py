# Import module files
from . import models
from . import services
from . import controllers

# Import Python libs
import logging

# Import Odoo libs
from . import models
from odoo import api, SUPERUSER_ID
# from odoo.addons.ls_base.models.tools import install_uuid_postgres_extension

_logger = logging.getLogger(__name__)


def _migrate_delivery_carrier_uuid_field(cr, registry):
    """
    Set the delivery carriers UUID from the related product template UUID
    """

    env = api.Environment(cr, SUPERUSER_ID, {})
    # Try to install the UUID postgres module
    install_uuid_postgres_extension(env)

    _logger.info("Set the delivery carriers UUID from the related product template UUID")
    query = """
        UPDATE delivery_carrier dc
        SET uuid = pt.uuid
        FROM product_product pp
        JOIN product_template pt ON
        pt.id = pp.product_tmpl_id
        WHERE pp.id = dc.product_id;
        """
    env.cr.execute(query)
