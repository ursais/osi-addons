from odoo import fields, models


class StockCycleCount(models.Model):
    _inherit = 'stock.cycle.count'

    def action_create_inventory_adjustment(self):
        res = super().action_create_inventory_adjustment()
        # Copy followers to inventory adjustment.
        for cycle in self:
            cycle.stock_adjustment_ids.message_subscribe(cycle.cycle_count_rule_id.message_follower_ids.mapped('partner_id').ids)
        return res
