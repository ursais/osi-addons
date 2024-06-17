# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Add tariff field to product templates
    """

    _inherit = 'product.template'

    # COLUMNS #####
    tariff_percent = fields.Float(string='Tariff Percent', company_dependent=True)
    tariff_code_id = fields.Many2one(string='Tariff Code', comodel_name="tariff.code", company_dependent=True)
    # END #########
