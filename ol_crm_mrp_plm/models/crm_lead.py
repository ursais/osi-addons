# Import Odoo libs
from odoo import fields, models


class CRMLead(models.Model):
    """Add the ability to create Engineering Change Order's from Leads."""

    _inherit = "crm.lead"

    # COLUMNS ######

    eco_ids = fields.One2many("mrp.eco", "opportunity_id", string="ECO")
    eco_count = fields.Integer(string="ECOs", compute="_compute_eco_count")

    # END ##########
    # METHODS ##########

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

    # END ##########
