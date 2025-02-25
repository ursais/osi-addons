# Import Odoo libs
from odoo import fields, models


class CRMStage(models.Model):
    """Add tag_ids field to CRM Stage."""

    _inherit = "crm.stage"

    # COLUMNS ######

    tag_ids = fields.Many2many(
        "crm.tag",
        string="Sales Order Tags",
        help="Sales Orders created from an opportunity in this stage will inherit these tags",
    )

    # END ##########
