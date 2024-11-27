from odoo import api,models,fields

class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    rush_order = fields.Boolean("Rush Order", related="procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.rush_order", readonly=False)
    rush_order_sale_id = fields.Many2one(related="procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id")