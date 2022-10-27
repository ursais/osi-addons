# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models


class CrmTaskWizard(models.TransientModel):
    _name = "crm.task.wizard"
    _description = "CRM Task Wizard"

    def get_name(self):
        active_id = self._context.get("active_id")
        crm_brw = self.env["crm.lead"].browse(active_id)
        return crm_brw.name

    project_id = fields.Many2one("project.project", "Project")
    name = fields.Char("Task Name", default=get_name)

    def create_task(self):
        active_id = self._context.get("active_id")
        crm_brw = self.env["crm.lead"].browse(active_id)
        vals = {
            "name": self.name,
            "project_id": self.project_id.id or False,
            "opportunity_id": crm_brw.id or False,
            "partner_id": crm_brw.partner_id.id,
        }
        task_id = self.env["project.task"].create(vals)
        return {
            "name": _("Created Task"),
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "views": [[False, "form"]],
            "res_id": task_id.id,
        }
