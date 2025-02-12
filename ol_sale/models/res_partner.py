# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add new field to Partners."""

    _inherit = "res.partner"

    # COLUMNS #####

    account_manager_id = fields.Many2one(
        "res.users",
        string="Account Manager",
    )
    sale_order_tag_ids = fields.Many2many(
        comodel_name="crm.tag",
        relation="res_partner_tag_rel",
        column1="partner_id",
        column2="tag_id",
        string="Sale Order Tags",
    )

    # END #########
