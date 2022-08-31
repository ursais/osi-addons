from odoo import models, fields


class LoanOptions(models.Model):
    _name = 'loan.options'
    _description = 'create a new loan option in the system'
    _rec_name = 'loan_name'

    loan_name = fields.Char('Loan Name/Type')
    loan_apr = fields.Float('APR', digits=(2, 2))
    minimum_credit = fields.Integer('Minimum Credit')


