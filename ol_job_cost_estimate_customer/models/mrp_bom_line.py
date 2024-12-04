# Import Odoo libs
from odoo import fields, models


class MRPBoMLine(models.Model):
    """
    Inherit MRP BoM Line for adding fields.
    """

    _inherit = "mrp.bom.line"

    # COLUMNS ##########

    estimate_line_id = fields.Many2one("sale.estimate.line.job", string="Estimate Line")

    # END #########
