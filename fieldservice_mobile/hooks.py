# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    # Check for existing res config setting
    env = api.Environment(cr, SUPERUSER_ID, {})
    config_settings_rec = env['res.config.settings'].search([])
    if not config_settings_rec:
        cr.execute("""
                    INSERT INTO res_config_settings (
                        module_fieldservice_isp_flow,
                        company_id)
                    VALUES (False, env.user.company_id.id);""",
                   )
