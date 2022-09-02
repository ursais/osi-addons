import random

from odoo import models, fields
from odoo.exceptions import UserError


class NewApplication(models.Model):
    _name = 'new.application'
    _description = 'create a new loan application in the system'
    applicant = fields.Many2one('new.applicant', string='Applicant')
    loan_type = fields.Many2one('loan.options', string='Loan type')
    _rec_name = 'applicant'

    loan_term = fields.Selection([('2', '2 years'), ('5', '5 years'),
                                  ('10', '10 years')], string='Loan term')
    applicant_credit = fields.Integer(related='applicant.applicant_credit')
    applicant_income = fields.Integer(related='applicant.monthly_income')
    progress_state = fields.Selection([('dft', 'Draft'),
                                       ('submit', 'Submitted'),
                                       ('approved', 'Approved'),
                                       ('rejected', 'Rejected')
                                       ], default='dft')

    determined_status = fields.Char('Determination', readonly=True)

    def button_submit(self):
        self.progress_state = 'submit'

        # get credit requirements from loan options model
        credit_score = self.loan_type.minimum_credit

        if credit_score < self.applicant_credit:
            self.determined_status = "Approved"
        else:
            self.determined_status = "Rejected"

    def button_approve(self):

        # TODO
        # save contact id in a new field
        # create smart button for contact

        if self.env['res.partner'].search([('vat', '=', self.applicant.ssn)]):
            raise UserError("Approved application already exists")
        else:
            self.progress_state = 'approved'

        contact = {'name': self.applicant.name,
                   'company_type': 'person',
                   'city': self.applicant.city,
                   'street': self.applicant.street_address,
                   'street2': self.applicant.street_address2,
                   'zip': self.applicant.zip,
                   'phone': self.applicant.phone,
                   'email': self.applicant.email,
                   'vat': self.applicant.ssn}

        self.env['res.partner'].create(contact)

    def button_reject(self):
        self.progress_state = 'rejected'
