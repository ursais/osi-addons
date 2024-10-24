# Import Python libs

# Import Odoo libs
from odoo import models, fields


class ExternalSystem(models.Model):
    _name = "external.system"
    _description = "External systems integrated with Odoo"

    _sql_constraints = [
        (
            "external_system_message_source_string_uniq",
            "UNIQUE(message_source_string)",
            "Message source string must be unique among External Systems!",
        )
    ]

    # COLUMNS #######
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description", required=False)
    message_source_string = fields.Char(string="Message Source String", required=True)
    enable_upsert = fields.Boolean(
        string="Enable Upserts", help="Enable upserts from this system", default=True
    )
    # END COLUMNS ###
