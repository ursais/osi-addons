# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    helpdesk_ticket_task_line = fields.One2many(
        "helpdesk.ticket.task",
        "ticket_id",
        string="Ticket Tasks",
    )


class HelpdeskTicketTask(models.Model):
    _name = "helpdesk.ticket.task"
    _description = "Helpdesk Ticket Task"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
    )
    project_id = fields.Many2one(related="ticket_id.project_id", string="Project")
    task_id = fields.Many2one(
        "project.task",
        string="Task",
    )
    user_id = fields.Many2one(
        related="task_id.user_id",
        string="Assigned to",
    )
    planned_hours = fields.Float(
        string="Planned Hours",
        related="task_id.planned_hours",
    )
    effective_hours = fields.Float(
        string="Actual Hours",
        related="task_id.effective_hours",
    )
