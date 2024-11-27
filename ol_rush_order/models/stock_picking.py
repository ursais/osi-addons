from odoo import api,models,fields

class ProductTemplate(models.Model):

    _inherit = 'stock.picking'

    rush_order = fields.Boolean("Rush Order",related="sale_id.rush_order")

    