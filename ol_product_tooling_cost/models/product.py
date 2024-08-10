# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Add tooling cost field to product templates
    """

    _inherit = "product.template"

    # COLUMNS #####
    tooling_cost = fields.Float(
        string="Tooling Cost",
        company_dependent=True,
        help="Non-recurring engineering costs.",
    )
    defrayment_cost = fields.Float(
        string="Defrayment Cost",
        company_dependent=True,
        help="Project costs to be recouped over the lifecycle of the product.",
    )
    # END #########
