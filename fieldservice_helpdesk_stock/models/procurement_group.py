# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    helpdesk_ticket_id = fields.Many2one("helpdesk.ticket", "Ticket")
