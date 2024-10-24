# Import Python libs

# Import Odoo libs
from odoo import models, fields


class WebhookClient(models.Model):
    """
    API Clients
    """

    _name = "api.client"
    _description = "API Client"

    _sql_constraints = [
        (
            "api_client_name_uniq",
            "UNIQUE(name)",
            "Api Client Name must be unique between all API Clients",
        )
    ]
    # COLUMNS #######
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description", required=False)
    # TODO: It would be a nice upgrade if we could get this value from Google Secret Manager
    #       instead of needing to set this manually through ODOO UI and also in Google Secret Manager
    # We have a ticket to address this: https://logicsupply.atlassian.net/browse/DEV-19548
    api_key = fields.Char(
        string="API key", copy=False, default="change-me-based-on-passbolt"
    )
    # END COLUMNS ###
