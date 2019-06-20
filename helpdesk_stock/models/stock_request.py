# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")
