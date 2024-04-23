# -*- coding: utf-8 -*-
# Part of Softhealer Technologies
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_pro_code_from_so = fields.Boolean(
        "Want to add Product Code from Sale Order")
