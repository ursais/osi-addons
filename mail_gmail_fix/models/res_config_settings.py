# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Extend res.config.settings to add missing google_gmail_client_identifier field.
    
    This field is required by Gmail integration modules but was missing from the
    database schema, causing errors when accessing email server settings.
    """
    _inherit = "res.config.settings"

    google_gmail_client_identifier = fields.Char(
        string="Google Gmail Client Identifier",
        help="Google OAuth Client Identifier for Gmail integration",
        config_parameter="mail.google_gmail_client_identifier",
    )
