# Import Odoo libs
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    # COLUMNS ###

    candidate_sale = fields.Boolean(
        string="Candidate to add to Quote",
    )
    candidate_sale_confirm = fields.Boolean(
        string="Candidate to be Sold",
    )
    candidate_purchase = fields.Boolean(
        string="Candidate to be Purchase",
    )
    candidate_manufacture = fields.Boolean(
        string="Candidate to be Manufacture",
    )
    candidate_component_manufacture = fields.Boolean(
        string="Candidate to be a MO Component",
    )
    candidate_bom = fields.Boolean(
        string="Candidate to be on a BoM",
    )
    candidate_ship = fields.Boolean(
        string="Candidate to be Ship",
    )

    # END #######
