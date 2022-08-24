from odoo import models, fields


class NewApplication(models.Model):
    _name = 'new.application'
    _description = 'create a new loan application in the system'

    applicant = fields.One2many(comodel_name='loan.options', inverse_name='email')
    loan_type = fields.One2many(comodel_name='new.applicant', inverse_name='loan_name')

    loan_term = fields.Selection([('2', '2 years'), ('5', '5 years'),
                                  ('10', '10 years')])
