# Copyright (C) 2020, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method")
