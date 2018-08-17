# -*- coding: utf-8 -*-
# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"
    
    account_discount_id = fields.Many2one('account.account',
                                          string="Discount Account",
                                          help="Account to use when creating "
                                               "the discount move line")
