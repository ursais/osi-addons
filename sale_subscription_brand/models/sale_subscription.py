# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    brand = fields.Many2one("res.partner", "Brand", domain="[('type', '=', 'brand')]")
