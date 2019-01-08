# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Subscription(models.Model):
    _inherit = 'sale.subscription'

    agreement_id = fields.Many2one('agreement', string="Agreement")
