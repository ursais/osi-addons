from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    credit_limit_amount = fields.Float(
        string="Credit Limit",
        related="company_id.credit_limit_amount",
        readonly=False,
        store=True,
    )
