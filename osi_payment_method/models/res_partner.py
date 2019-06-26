# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit="res.partner"

    payment_method = fields.Many2one("custom.payment.method", string="Payment Method")

        