from odoo.addons.ol_pim.utils.update_attribute_data import (
    load_attribute_set_group_option_csv_data,
)
import logging

_logger = logging.getLogger(__name__)


def load_attribute_csv_data(env):
    """Main Function to Import Data in Correct Order"""
    _logger.warning("*************** STARTING CSV IMPORT ***************")

    load_attribute_set_group_option_csv_data(env)

    _logger.warning("*************** CSV IMPORT COMPLETE ***************")
