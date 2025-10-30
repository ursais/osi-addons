# Import Odoo libs
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # COLUMNS ###

    rush_lead_time = fields.Integer(
        string="Rush Lead Time",
        help="Lead time (in days) to handle rush orders, specific per company.",
    )

    # END #######
