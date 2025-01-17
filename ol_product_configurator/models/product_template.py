# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Extend product.template with additional fields and logic for managing
    visibility in configuration wizard.
    """

    _inherit = "product.template"

    # COLUMNS ##########
    default_code = fields.Char(
        "Internal Reference",
        compute="",
        inverse="",
        store=True,
    )
    company_ids_display = fields.Many2many(
        comodel_name="res.company",
        string="Enabled Companies",
        help=(
            """Used for eCommerce: If set, the product is limited to be sold
            only in these regions."""
        ),
    )

    # END ##########
