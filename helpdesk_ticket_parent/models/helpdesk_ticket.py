# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    parent_id = fields.Many2one("helpdesk.ticket", string="Parent")
    child_ids = fields.One2many("helpdesk.ticket", "parent_id", string="Children")
