# Import Odoo libs
from odoo import fields, models


class PLMECOType(models.Model):
    """
    Add field to PLM ECO Type
    """

    _inherit = "mrp.eco.type"

    # COLUMNS #####

    component_replacement = fields.Boolean(
        string="Component Replacement",
        help="""When enabled, the component replacement functionality is enabled
          for this ECO Type adding a replace with component field and populates BoM's
          that will be updated with the component replacement.""",
    )

    # END #########
