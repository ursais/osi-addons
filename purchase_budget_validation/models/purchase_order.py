# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    over_budget = fields.Boolean(
        compute="_compute_over_budget_po", string="Over Budget"
    )

    def _compute_over_budget_po(self):
        for rec in self:
            rec.over_budget = rec.check_budget(notify=False)

    def check_budget(self, notify=False):
        message = ""
        users = None
        over_budget = False
        for po_line in self.order_line:
            budget_lines = po_line._get_budget_lines()
            for b_line in budget_lines:
                if b_line.over_budget:
                    users += b_line.crossovered_budget_id.user_id
                    message += _(
                        "This order is over budget %s / %s (%s):"
                        "<br/>%s + %s + %s = %s > %s.<br/>"
                        % (
                            b_line.crossovered_budget_id.name,
                            b_line.name,
                            b_line.crossovered_budget_id.user_id.name,
                            abs(b_line.practical_amount),
                            abs(b_line.committed_amount),
                            abs(b_line.uncommitted_amount),
                            abs(b_line.practical_amount) + abs(
                                b_line.committed_amount) + abs(
                                b_line.uncommitted_amount),
                            abs(b_line.planned_amount),
                        )
                    )
        if message:
            over_budget = True
        if notify:
            for user in users:
                self.message_subscribe(partner_ids=user.partner_id.ids)
            self.message_post(body=message)
        return over_budget

    def button_confirm(self):
        for rec in self:
            if rec.over_budget:
                raise ValidationError(
                    _(
                        "You cannot confirm the purchase order "
                        "as one budget would go over the planned amount. "
                        "Please check the chatter for more details."
                    )
                )
            else:
                super(PurchaseOrder, rec).button_confirm()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.check_budget(notify=True)
        return res

    def write(self, vals):
        res = super().write(vals)
        for po in self:
            po.check_budget(notify=True)
        return res
