# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False
    )

    def _prepare_move_line(self,line):
        res = super(HrExpense, self)._prepare_move_line(line)
        res['analytic_segment_one']=line.get('analytic_segment_one')
        res['analytic_segment_two']=line.get('analytic_segment_two')
        return res

    @api.multi
    def _prepare_move_line_value(self):
        res = super(HrExpense, self)._prepare_move_line_value()
        res['analytic_segment_one']=self.analytic_segment_one.id
        res['analytic_segment_two']=self.analytic_segment_two.id
        return res


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False
    )
