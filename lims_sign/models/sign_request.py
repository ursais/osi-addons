from odoo import fields, models


class SignRequest(models.Model):
    _inherit = "sign.request"

    lims_order_id = fields.Many2one(
        "lims.order", string="LIMS Order", ondelete="cascade"
    )
