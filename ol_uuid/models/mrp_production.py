# Import Odoo libs
from odoo import models


class MrpProduction(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'mrp.production'
    _inherit = ['mrp.production', 'res.uuid']
