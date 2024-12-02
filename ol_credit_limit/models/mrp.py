# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MRPProduction(models.Model):
    """
    Inherit MRP Prodduction Object to add Credit Limit.
    """

    _inherit = "mrp.production"

    credit_hold = fields.Boolean(
        "Credit Hold", related="sale_order_id.credit_hold", readonly=True
    )

    def action_confirm(self):
        for mo in self:
            if mo.sale_order_id and mo.sale_order_id.credit_hold:
                raise UserError(
                    _("Manufacturing cannot proceed due to customer's credit hold.")
                )
        return super().action_confirm()

    def button_plan(self):
        for mo in self:
            if mo.sale_order_id and mo.sale_order_id.credit_hold:
                raise UserError(
                    _("Manufacturing cannot proceed due to customer's credit hold.")
                )
        return super().button_plan()

    def button_mark_done(self):
        for mo in self:
            if mo.sale_order_id and mo.sale_order_id.credit_hold:
                raise UserError(
                    _("Manufacturing cannot proceed due to customer's credit hold.")
                )
        return super().button_mark_done()
