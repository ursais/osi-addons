# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import date

from odoo import _, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        # budget_post_obj = self.env["account.budget.post"]
        # budget_lines_obj = self.env["crossovered.budget.lines"]
        for rec in self:
            # message = ""
            # for po_line in rec.order_line:
            #     domain_budget_lines = [
            #         ("date_from", "<=", date.today()),
            #         ("date_to", ">=", date.today()),
            #         ("crossovered_budget_state","=","confirm"),
            #         '|',]
            #     if po_line.account_analytic_id:
            #         domain_budget_lines.append(
            #             ("analytic_account_id", "=", po_line.account_analytic_id.id))
            #     budget_post_id = budget_post_obj.search(
            #         [("account_ids", "in",
            #         po_line.product_id.property_account_expense_id.ids or
            #         po_line.product_id.categ_id.property_account_expense_categ_id.ids)],
            #         limit=1)
            #     if budget_post_id:
            #         domain_budget_lines.append(
            #             ("general_budget_id", "=", budget_post_id.id))

            #     budget_lines_ids = budget_lines_obj.search(domain_budget_lines)
            #     budget_limit_exceed = True
            #     for budget_line in budget_lines_ids:
            #         if po_line.price_subtotal >
            #                 (budget_line.planned_amount -
            #                 abs(budget_line.practical_amount)):
            #             message += _("<p>Purchase Order Line with Product %s is over
            #             budget %s %s%s > %s%s </p>" %
            #                          (po_line.product_id.name,
            #                          budget_line.crossovered_budget_id.name,
            #                          po_line.price_subtotal,
            #                          po_line.currency_id.symbol,
            #                          (budget_line.planned_amount -
            #                          abs(budget_line.practical_amount)),
            #                          budget_line.currency_id.symbol,))
            #         else:
            #             budget_limit_exceed = False
            #     if not budget_limit_exceed:
            #         po_line.has_budget_limit = True

            rec._check_budget_by_analytic_account()

            # group = self.env.ref(
            #     'purchase.group_purchase_manager')
            # po_user = self.env["res.users"].search([('groups_id', 'in', group.ids)])
            # if po_user:
            #     rec.message_subscribe(partner_ids=po_user.partner_id.ids)
            # rec.message_post(body=message)
            if any(rec.order_line.filtered(lambda x: x.has_budget_limit is False)):
                rec.state = "to approve"
            else:
                return super(PurchaseOrder, self).button_confirm()

    def _check_budget_by_analytic_account(self):
        budget_lines_obj = self.env["crossovered.budget.lines"]
        budget_post_obj = self.env["account.budget.post"]
        for analytic_acc_id in self.order_line.mapped("account_analytic_id"):
            price_total_lines = sum(
                [
                    line.price_subtotal
                    for line in self.order_line.filtered(
                        lambda x: x.account_analytic_id.id == analytic_acc_id.id
                    )
                ]
            )
            effected_lines_acc = list(
                {
                    line.product_id.property_account_expense_id.id
                    if line.product_id.property_account_expense_id
                    else line.product_id.categ_id.property_account_expense_categ_id.id
                    for line in self.order_line.filtered(
                        lambda x: x.account_analytic_id.id == analytic_acc_id.id
                    )
                }
            )
            domain_budget_lines = [
                ("date_from", "<=", date.today()),
                ("date_to", ">=", date.today()),
                ("crossovered_budget_state", "=", "confirm"),
                "|",
                ("analytic_account_id", "=", analytic_acc_id.id),
            ]
            budget_post_id = budget_post_obj.search(
                [("account_ids", "in", effected_lines_acc)], limit=1
            )
            if budget_post_id:
                domain_budget_lines.append(
                    ("general_budget_id", "=", budget_post_id.id)
                )
            budget_lines_ids = budget_lines_obj.search(domain_budget_lines)

            budget_limit_exceed = True
            message = ""
            for budget_line in budget_lines_ids:
                if price_total_lines > (
                    budget_line.planned_amount - abs(budget_line.practical_amount)
                ):
                    message += _(
                        "<p>Order lines with %s Analytic Account are over budget: "
                        "%s%s > %s%s.</p>"
                        % (
                            analytic_acc_id.name,
                            price_total_lines,
                            self.currency_id.symbol,
                            (
                                budget_line.planned_amount
                                - abs(budget_line.practical_amount)
                            ),
                            budget_line.currency_id.symbol,
                        )
                    )
                else:
                    budget_limit_exceed = False

            if not budget_limit_exceed:
                for line in self.order_line.filtered(
                    lambda x: x.account_analytic_id.id == analytic_acc_id.id
                ):
                    line.has_budget_limit = True

            group = self.env.ref("purchase.group_purchase_manager")
            po_user = self.env["res.users"].search([("groups_id", "in", group.ids)])
            if po_user:
                self.message_subscribe(partner_ids=po_user.partner_id.ids)
            self.message_post(body=message)
