# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    payment_method = fields.Many2one(
        "account.payment.method",
        string="Company Credit Card")

    @api.multi
    def action_submit_expenses(self):
        res = super(HrExpense, self).action_submit_expenses()
        for picking in self:
            if res and picking.payment_method:
                # Update Payment method in context
                res['context'].update(
                    {'default_payment_method': self.payment_method.id})
                # check context if called from submit to manager button
                if 'update_hr_expense_sheet' in self._context:
                    vals = {
                        'state': 'submit',
                        'payment_method': self.payment_method.id,
                        'expense_line_ids':
                            [(6, 0, [line.id for line in self])],
                        'employee_id': self[0].employee_id.id,
                        'name': self[0].name if len(self.ids) == 1 else ''}
                    new_expense = self.env['hr.expense.sheet'].create(vals)
                    # Redirect to expense sheet view
                    return {
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'hr.expense.sheet',
                        'target': 'current',
                        'res_id': new_expense.id}
                else:
                    break
        # check context if called from submit to manager button
        if 'update_hr_expense_sheet' in self._context:
            # update context to make hr expense sheet in submit state
            exp_ids = [line.id for line in self]
            vals = {
                'state': 'submit',
                'expense_line_ids': [(6, 0, exp_ids)],
                'employee_id': self[0].employee_id.id,
                'name': self[0].name if len(self.ids) == 1 else ''}
            new_expense = self.env['hr.expense.sheet'].create(vals)
            # Redirect to expense sheet view
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'hr.expense.sheet',
                'target': 'current',
                'res_id': new_expense.id}
        return res


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    payment_method = fields.Many2one("account.payment.method",
                                     string="Company Card used to Pay")
    emp_manager = fields.Many2one(related='employee_id.parent_id',
                                  string='Employee Manager')
    accounting_date = fields.Date(string='Accounting Date')

    @api.multi
    def approve_expense_sheets(self):
        for expense in self:
            supervisor = expense.employee_id.expense_manager_id or \
                expense.employee_id.parent_id
            supervisor_ids = []
            while supervisor:
                if supervisor.user_id:
                    supervisor_ids.append(supervisor.user_id)
                supervisor = supervisor.parent_id

            if expense.employee_id.user_id == expense.env.user:
                raise UserError(_("You are not allowed to approve your own "
                                  "expense!"))
            if expense.employee_id.expense_manager_id != expense.env.user:
                if len(supervisor_ids) and expense.env.user not in supervisor_ids:
                    raise UserError(_("You are not allowed to approve expenses "
                                    "outside of your department!"))
        return super(HrExpenseSheet, self).approve_expense_sheets()
