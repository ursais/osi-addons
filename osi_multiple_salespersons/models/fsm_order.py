from odoo import models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    def build_invoice(self):
        res = super().build_invoice()
        account_move_id = self.env["account.move"].search(
            [
                ("sale_order_id", "=", self.sale_id.id),
                ("fsm_order_ids", "in", self.ids),
                ("move_type", "=", "out_invoice"),
            ],
            limit=1,
        )
        if account_move_id and self.sale_id:
            account_move_id.sale_user_ids = [(6, 0, self.sale_id.sale_user_ids.ids)]
        return res

    def build_bill(self):
        res = super().build_bill()
        account_move_id = self.env["account.move"].search(
            [
                ("sale_order_id", "=", self.sale_id.id),
                ("fsm_order_ids", "in", self.ids),
                ("move_type", "=", "in_invoice"),
            ],
            limit=1,
        )
        if account_move_id and self.sale_id:
            account_move_id.sale_user_ids = [(6, 0, self.sale_id.sale_user_ids.ids)]
        return res
