import random

from odoo import models, fields, api


class NewApplication(models.Model):
    _name = 'new.application'
    _description = 'create a new loan application in the system'
    applicant = fields.Many2one('new.applicant', string='Applicant')
    loan_type = fields.Many2one('loan.options', string='Loan type')

    loan_term = fields.Selection([('2', '2 years'), ('5', '5 years'),
                                  ('10', '10 years')], string='Loan term')
    applicant_credit = fields.Integer(related='applicant.applicant_credit')
    progress_state = fields.Selection([('dft', 'Draft'),
                                       ('submit', 'Submitted'),
                                       ('approved', 'Approved'),
                                       ('rejected', 'Rejected')
                                       ], default='dft')

    determined_status = fields.Char('Determination')

    def button_submit(self):
        self.progress_state = 'submit'

        get_min_credit = fields.Many2one('loan.options')
        # simulate using credit API to get credit score

        # get credit requirements from loan options model
        credit_score = self.loan_type.minimum_credit

        if credit_score < self.applicant_credit:
            self.determined_status = "Approved"
        else:
            self.determined_status = "Rejected"

    def button_approve(self):
        # TODO
        # search for other loan apps and if approved throw error

        # TODO
        # create a contact in odoo if approved use (res partners)
        self.progress_state = 'approved'

    def button_reject(self):
        self.progress_state = 'rejected'
