from odoo import api, SUPERUSER_ID
from odoo.addons.ol_pim.utils.update_attribute_data import (
    load_attribute_set_group_option_csv_data,
)
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger = logging.getLogger(__name__)
    _logger.warning("*************** STARTING CSV IMPORT ***************")

    load_attribute_set_group_option_csv_data(env)

    _logger.warning("*************** CSV IMPORT COMPLETE ***************")
