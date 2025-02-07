# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Traveler related fields
    """

    _inherit = "product.template"

    # COLUMNS #####

    template_check_ids = fields.Many2many(
        comodel_name="mrp.assembly.check",
        string="Assembly Checks",
    )
    template_bios_name = fields.Char(string="BIOS Name")
    work_documentation_url = fields.Char(
        string="Work Documentation URL",
    )

    # END #########
