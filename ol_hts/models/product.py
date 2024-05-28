# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """ Add field to product.template to store HTS codes """

    _inherit = "product.template"

    # COLUMNS ###

    hts_code_id = fields.Many2one(string='HTS Code', comodel_name='product.hts')

    # END #######


class ProductHTS(models.Model):
    """ Data object for HTS codes."""

    _description = 'Tariff Codes'
    _name = "product.hts"
    _order = "name"

    # COLUMNS ###

    name = fields.Char(string='Category', size=64, required=True)
    short_description = fields.Char(string='Short Description', size=255)
    description = fields.Text(string='Description')
    schedule_b = fields.Char(string='Schedule B', size=24)
    property_product_hts_hts = fields.Char(string='HTS', size=24, required=True, company_dependent=True)
    property_product_hts_label = fields.Char(
        string='PO Label', size=24, required=True, company_dependent=True
    )

    # END #######
