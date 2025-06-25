# Import Odoo libs
from odoo import models

class MrpBom(models.Model):
    """
    Add uuid to mrp.bom
    """

    _name = 'mrp.bom'
    _inherit = ['mrp.bom', 'res.uuid']
    
class MrpBomLine(models.Model):
    """
    Add uuid to mrp.bom.line
    """

    _name = 'mrp.bom.line'
    _inherit = ['mrp.bom.line', 'res.uuid']