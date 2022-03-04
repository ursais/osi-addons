# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    opportunity_id = fields.Many2one("crm.lead")
    opportunity_count = fields.Integer(compute="_compute_opportunity_count")

    @api.depends("opportunity_id")
    def _compute_opportunity_count(self):
        for task in self:
            task.opportunity_count = len(task.opportunity_id)

    def action_view_opportunity(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "crm.crm_lead_action_pipeline"
        )
        form_view = [(self.env.ref("crm.crm_lead_view_form").id, "form")]
        if "views" in action:
            action["views"] = form_view
        action["res_id"] = self.opportunity_id.id
        return action
