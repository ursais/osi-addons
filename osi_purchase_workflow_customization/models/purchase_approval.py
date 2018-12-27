# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseApproval(models.Model):
    _name = 'purchase.approval'
    _order = 'approval_amount desc'
    _description = 'Purchase Order Approval'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
    )
    job_id = fields.Many2one(comodel_name='hr.job', string='Role')
    approval_amount = fields.Float(string='Approval amount')
    co_approval_amount = fields.Float(string='Co-Approval amount')
    user_id = fields.Many2one(
        related='employee_id.user_id',
        string='Related User'
    )
    po_type = fields.Selection(
        selection=[('inventory', 'Inventory'),
                   ('non-inventory', 'Non Inventory')],
        string='PO Type',
        default='inventory',
    )

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id
