# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def _compute_task_count(self):
        task_obj = self.env["project.task"]
        self.task_number = task_obj.search_count(
            [("opportunity_id", "in", [a.id for a in self])]
        )

    task_number = fields.Integer(compute="_compute_task_count", string="Tasks")
    task_id = fields.Many2one("project.task")

    def open_task_wiz(self):
        view_id = self.env.ref("osi_crm_project.view_crm_task_wizard_form").id
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Task"),
            "res_model": "crm.task.wizard",
            "target": "new",
            "view_mode": "form",
            "views": [[view_id, "form"]],
        }
