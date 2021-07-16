# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    project_task_ticket_line = fields.One2many(
        "project.task.ticket",
        "task_id",
        string="Task Tickets",
    )


class ProjectTaskTicket(models.Model):
    _name = "project.task.ticket"
    _description = "Project Task Ticket"

    task_id = fields.Many2one(
        "project.task",
        string="Task",
    )
    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
    )
    project_id = fields.Many2one(related="task_id.project_id", string="Project")
    user_id = fields.Many2one(related="ticket_id.user_id", string="Assigned to")
