# Import Odoo Libs
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # COLUMNS #####

    hot_ar_grace_period = fields.Integer(
        string="Hot AR Grace Period",
        related="company_id.hot_ar_grace_period",
        readonly=False,
        help="""Places holds on customer orders when invoices are not paid
         within grace period of being due."""
    )

    # END #########
