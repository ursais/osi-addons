# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    is_company_credit_limit = fields.Boolean("Aggregate company Credit limit")
