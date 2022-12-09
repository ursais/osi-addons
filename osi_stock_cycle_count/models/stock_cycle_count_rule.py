from odoo import fields, models


class StockCycleCountRule(models.Model):
    _name = 'stock.cycle.count.rule'
    _inherit = ['stock.cycle.count.rule', 'mail.thread']

    notify_before = fields.Integer('Notify before in days')
