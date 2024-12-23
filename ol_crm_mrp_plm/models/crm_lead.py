from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = "crm.lead"

    eco_ids = fields.One2many("mrp.eco", "opportunity_id", string="ECO")
    eco_count = fields.Integer(string="ECO Count", compute="_compute_eco_count")

    def _compute_eco_count(self):
        for lead in self:
            lead.eco_count = len(lead.eco_ids)

    def action_view_eco(self):
        eco_ids = self.eco_ids
        action = self.env.ref("mrp_plm.mrp_eco_action_main").read()[0]
        action["context"] = {"create": False}
        if len(eco_ids) == 1:
            action["views"] = [
                (
                    self.env.ref("mrp_plm.mrp_eco_view_form").id,
                    "form",
                )
            ]
            action["res_id"] = eco_ids.id
        else:
            action["domain"] = [("id", "in", eco_ids.ids)]
        return action
