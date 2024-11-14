# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    preferred_payment_method_id = fields.Many2one(related="move_id.preferred_payment_method_id", store=True)
