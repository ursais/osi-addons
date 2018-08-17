# -*- coding: utf-8 -*-
# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    store_credit_product_id = fields.Many2one('product.product', string='Store Credit')
    gift_card_product_id = fields.Many2one('product.product', string='Gift Card')
