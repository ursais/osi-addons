from odoo import fields, models


class ResCompany(models.Model):
    """
    Add new fields to Res Company
    """

    _inherit = "res.company"

    # COLUMNS #####

    blanket_order_release_days = fields.Integer(
        string="Days Before Scheduled Date to Release Blanket Orders",
        default=30,
        help="Number of days before the scheduled "
        "date to release blanket orders into sale orders.",
    )
    # END #########
