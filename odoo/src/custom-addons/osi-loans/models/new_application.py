from odoo import models, fields


class NewApplication(models.Model):
    _name = 'new.application'
    _description = 'create a new loan application in the system'

    applicant = fields.Many2one('new.applicant', string='Applicant')
    loan_type = fields.Many2one('loan.options', string='Loan type')

    loan_term = fields.Selection([('2', '2 years'), ('5', '5 years'),
                                  ('10', '10 years')], string='Loan term')

    progress_state = fields.Selection([('draft', 'Draft'),
                                       ('submitted', 'Submitted'),
                                       ('approved', 'Approved'),
                                       ('rejected', 'Rejected'),
                                       ], required=True, default='draft',
                                      string="Progress")

    def button_submit(self):
        self.progress_state = 'submitted'
