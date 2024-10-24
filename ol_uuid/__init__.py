# Import module files
from . import models

# Import Python libs
import os
import logging

# Import Odoo libs
from odoo import api, SUPERUSER_ID
from odoo.addons.ol_base.models.tools import install_uuid_postgres_extension

_logger = logging.getLogger(__name__)


def _run_install_scripts(env):
    _generate_uuids(env)


def _generate_uuids(env):
    """
    Copy over the existing UUIDs from the rabbit tables to the new core odoo tables
    """

    # Set the environment
    env = api.Environment(env.cr, SUPERUSER_ID, {})

    # Try to install the UUID postgres module
    install_uuid_postgres_extension(env)

    # Add UUIDs to tables
    tables = ["sale_order", "res_partner"]
    for table in tables:
        query = f"""ALTER TABLE {table} ADD COLUMN IF NOT EXISTS uuid uuid;"""
        _logger.info(f"res.uuid: Add UUIDs to table: {table}")
        query = f"""
        UPDATE {table}
        SET uuid = uuid_generate_v4()
        WHERE uuid IS NULL;
        """
        env.cr.execute(query)
