# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cleared_cc_account = fields.Boolean(
        'CC Cleared?',
        help='Check if the transaction has cleared from the bank')
    cc_rec_statement_id = fields.Many2one(
        'cc.rec.statement', string='CC Rec Statement',
        help="The credit card reconciliation statement linked with the journal"
             " item")
