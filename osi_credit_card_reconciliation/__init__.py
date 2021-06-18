# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from . import models
from odoo import api, SUPERUSER_ID


def init_settings(env):
    """Activate the Multi Currency by default."""
    curr_config_id = env["res.config.settings"].create({"group_multi_currency": True})
    # We need to call execute, otherwise the "implied_group" in fields are not
    # processed.
    curr_config_id.execute()


def post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    init_settings(env)
