# Import Odoo libs
from odoo import fields, models


class MrpProduction(models.Model):
    """Add new field to Manufacturing Orders."""

    _inherit = "mrp.production"

    # COLUMNS #####

    mrp_note = fields.Text(
        string="Manufacturing Note",
        related="sale_order_id.mrp_note",
        store=True,
    )
    date_change_exception = fields.Boolean(string="Customer Request Date Change Proposed", default=False)


    # END #########
