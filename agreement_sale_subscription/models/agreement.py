# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Agreement(models.Model):
    _inherit = 'agreement'

    subscription_id = fields.Many2one('sale.subscription',
                                      string="Subscription")
