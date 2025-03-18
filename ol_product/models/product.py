# Import Odoo Libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Updates to product template to add Row,Rack,and Case fields
    """

    _inherit = "product.template"

    # COLUMNS #####
    loc_rack = fields.Char(string="Rack")
    loc_row = fields.Char(string="Row")
    loc_case = fields.Char(string="Case")
    # END #########