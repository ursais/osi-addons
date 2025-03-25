# Import Odoo libs
from odoo import fields, models


class RepairOrder(models.Model):
    """Add warranty fields to Repair Order"""

    _inherit = "repair.order"

    # COLUMNS ###

    warranty_expiration_date = fields.Date(
        string="Warranty Expiration Date",
        related="lot_id.warranty_expiration_date",
        help="Warranty expires on this date.",
    )

    # END #######
