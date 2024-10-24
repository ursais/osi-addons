# Import Odoo libs
from odoo import fields, models, api


class GraphQLSettings(models.TransientModel):
    """
    Handles default Queue Search settings.
    """

    _inherit = "res.config.settings"

    # COLUMNS #######
    reverse_identity_key = fields.Boolean(
        string="Reverse identity key",
        help=(
            "Invert the logic of the Queue Job identity key feature. If jobs have unique identifying keys,"
            " jobs that are triggered to run (perform) while other jobs exists with the same key that have"
            " not yet been run, the run of this earlier job will be skipped. This was we can group jobs for"
            " similar identity keys while also ensure that we run the given functionalities at the latest"
            " possible time."
        ),
        config_parameter="ol_queue_job.reverse_identity_key",
    )

    # END #########
