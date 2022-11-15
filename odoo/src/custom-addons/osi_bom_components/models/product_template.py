from odoo import fields,models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bom_components = fields.One2many('mrp.bom.line', string="Bom Components")
