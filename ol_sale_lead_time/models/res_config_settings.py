from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # COLUMNS ###

    rush_lead_time = fields.Integer(
        string="Rush Lead Time",
        related="company_id.rush_lead_time",
        readonly=False,
        help="Lead time (in days) to handle rush orders, specific per company.",
    )
    # END #######
