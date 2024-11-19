# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Adding fields to product templates.
    """

    _inherit = "product.template"

    # COLUMNS ##########

    public_destination = fields.Selection(
        [
            ("not_public", "Not Public"),
            ("b2b", "B2B"),
            ("b2c", "B2C"),
            ("b2b_b2c", "B2B + B2C"),
        ],
        string="Public Destination",
        default="not_public",
    )
    company_ids_display = fields.Many2many(
        "res.company",
        string="Enabled Companies",
        help="To be used for eCommerce:"
        " If set, the product is limited to only be sold in these regions.",
    )

    # END ##########
