# Import Odoo libs
from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = "mrp.production"


    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing', 'move_raw_ids.picked')
    def _compute_state(self):
        res = super()._compute_state()
        for production in self:
            if production.state in ('progress','to_close'):
                sale_order_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id
                if sale_order_ids:
                    order_state = self.env.ref('ol_sale_substate.base_substate__sent').id
                    sale_order_ids.write({"substate_id":order_state})
        return res