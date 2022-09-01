from datetime import datetime
import random
from odoo.exceptions import UserError

from odoo import models, fields, api


class NewApplicant(models.Model):
    _name = 'new.applicant'
    _description = 'create a new applicant in the system'

    name = fields.Char('Name', required=True)
    dob = fields.Date('Date of Birth', required=True)
    age = fields.Integer('Age')
    MINIMUM_AGE = 18

    phone = fields.Char('Phone number', required=True)
    email = fields.Char('Email', required=True)
    street_address = fields.Text('Street Address', required=True)
    street_address2 = fields.Text('Street 2', required=False)
    city = fields.Char('City', required=True)
    state = fields.Selection([
        ('AL', 'AL'), ('AK', 'AK'), ('AZ', 'AZ'), ('AR', 'AR'), ('CA', 'CA'), ('CO', 'CO'), ('CT', 'CT'), ('DE', 'DE'),
        ('DC', 'DC'), ('FL', 'FL'), ('GA', 'GA'), ('HI', 'HI'), ('ID', 'ID'), ('IL', 'IL'), ('IN', 'IN'), ('IA', 'IA'),
        ('KS', 'KS'), ('KY', 'KY'), ('LA', 'LA'), ('ME', 'ME'), ('MD', 'MD'), ('MA', 'MA'), ('MI', 'MI'), ('MN', 'MN'),
        ('MS', 'MS'), ('MO', 'MO'), ('MT', 'MT'), ('NE', 'NE'), ('NV', 'NV'), ('NH', 'NH'), ('NJ', 'NJ'), ('NM', 'NM'),
        ('NY', 'NY'), ('NC', 'NC'), ('ND', 'ND'), ('OH', 'OH'), ('OK', 'OK'), ('OR', 'OR'), ('PA', 'PA'), ('RI', 'RI'),
        ('SC', 'SC'), ('SD', 'SD'), ('TN', 'TN'), ('TX', 'TX'), ('UT', 'UT'), ('VT', 'VT'), ('VA', 'VA'), ('WA', 'WA'),
        ('WV', 'WV'), ('WI', 'WI'), ('WY', 'WY')], string="State")

    zip = fields.Integer('Zip code')
    ssn = fields.Integer('SSN #')
    employment_status = fields.Selection([('Employed', 'Employed'), ('Unemployed', 'Unemployed'),
                                          ('Fixed', 'Fixed Income (SSI, Retirement Income)')],
                                         string='Employment Status')
    monthly_income = fields.Integer('Monthly income')
    employer = fields.Char('Employer')
    employer_number = fields.Char('Employer contact number')
    applicant_credit = fields.Integer("Applicant Credit", readonly=True)

    @api.model
    def create(self, vals):
        res = super(NewApplicant, self).create(vals)
        res.applicant_credit = random.randint(350, 800)
        return res

    def write(self, values):
        res = super(NewApplicant, self).write(values)
        if self.age < self.MINIMUM_AGE:
            raise UserError("Applicant age under 18")
        return res

    @api.onchange('dob')
    def check_valid_age(self):
        date = datetime.strptime(str(self.dob), "%Y-%m-%d")
        today_date = date.today()
        calculated_age = today_date.year - date.year
        self.age = calculated_age
