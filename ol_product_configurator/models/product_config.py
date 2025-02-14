# Import Odoo libs
from odoo import fields, models


class ProductConfigSession(models.Model):
    """
    Inherit product config session to add company field.
    """

    _inherit = "product.config.session"

    # COLUMNS ##########

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    # END ##########
