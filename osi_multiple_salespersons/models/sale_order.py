from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_user_ids = fields.Many2many("res.users", string="Additional Salesperson")

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.env.context.get(
            "default_partner_id"
        ) == self.partner_id.id and self.env.context.get("default_sale_user_ids"):
            self.sale_user_ids = self.env.context.get("default_sale_user_ids")
        else:
            self.sale_user_ids = (
                self.partner_id.sale_user_ids.ids
                or self.partner_id.commercial_partner_id.sale_user_ids.ids
                or False
            )
        return res

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update({"sale_user_ids": self.sale_user_ids.ids})
        return res
