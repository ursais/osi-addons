from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = super()._prepare_account_move_line(move)
        if self.product_id and self.product_id.type == 'consu':
            expense_account = self.product_id.product_tmpl_id._get_product_accounts().get('expense')
            input_account = self.product_id.product_tmpl_id._get_product_accounts().get('stock_input')
            res.update({'account_id': input_account.id})
        return res
