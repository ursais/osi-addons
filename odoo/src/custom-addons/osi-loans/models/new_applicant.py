from odoo import  models, fields, api

class applicant:
    _name = 'new.applicant'
    _description = 'applicant'

    fname = fields.Char('First name', required=True)
    lname = fields.Char('Last name', required=True)
    dob = fields.Date('Date of Birth')
    phone = fields.Char('Phone number', required=True)
    email = fields.Char('Email', required=True)
    street_address = fields.Text('Street Address', required=True)
    street_address2 = fields.Text('Street Address Line 2 (Optional)', required=False)
    state = fields.Selection([
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY',
        'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH',
        'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'], string="State")

    zip = fields.Integer('Zip code')
    ssn = fields.Integer('SSN #')
    employment_status = fields.Selection(['Employed', 'Unemployed', 'Fixed Income (SSI, Retirement Income)'])
    monthly_income = fields.Integer('Monthly income')
    employer = fields.Char('Employer')
    employer_number = fields.Char('Employer contact number')
