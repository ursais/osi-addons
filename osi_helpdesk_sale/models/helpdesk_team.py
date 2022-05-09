# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    use_sale_orders = fields.Boolean(string="Sales Orders")
