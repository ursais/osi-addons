# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskPhone(models.Model):
    _inherit = 'helpdesk.ticket'

    partner_phone = fields.Char(related='partner_id.phone', string="Phone")
