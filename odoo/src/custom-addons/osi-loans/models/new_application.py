import random

from odoo import models, fields, api
import odoo.exceptions


class NewApplication(models.Model):
    _name = 'new.application'
    _description = 'create a new loan application in the system'
    _inherit = "res.partner"
    applicant = fields.Many2one('new.applicant', string='Applicant')
    loan_type = fields.Many2one('loan.options', string='Loan type')

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

    @api.model
    def button_approve(self, vals):
        # TODO
        # search for other loan apps and if approved throw error
        # tie models together so that you cant delete applicant if application
        # is present

        # TODO
        # create a contact in odoo if approved use (res partners)
        # save contact id in a new field
        # create smart button for contact
        res = super(NewApplication, self).create(vals)

        if vals.has_key(self.applicant.ssn):
            pass
        else:
            self.progress_state = 'approved'

        res.name = self.applicant.name
        res.company_type = 'person'
        res.street = self.applicant.street_address
        res.street2 = self.applicant.street_address2
        res.zip = self.applicant.zip
        res.phone = self.applicant.phone
        res.email = self.applicant.email
        return res

    def button_reject(self):
        self.progress_state = 'rejected'
