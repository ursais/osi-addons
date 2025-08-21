# Import Odoo libs
from odoo import fields, models


class StockLot(models.Model):
    """
    Add fields and methods for MO smart button on serials
    """

    _inherit = "stock.lot"

    # COLUMNS #####

    production_count = fields.Integer("Production count", compute="_compute_mo_count")

    # END #########
    # METHODS #####

    def _compute_mo_count(self):
        for rec in self:
            rec.production_count = rec.env["mrp.production"].search_count(
                [("lot_producing_id", "=", rec.id)]
            )

    def action_view_mrp_production(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "mrp.mrp_production_action"
        )
        action["context"] = {}
        productions = self.env["mrp.production"].search(
            [("lot_producing_id", "=", self.id)]
        )
        if len(productions) > 1:
            action["domain"] = [("id", "in", productions.ids)]
        elif productions:
            action["views"] = [
                (self.env.ref("mrp.mrp_production_form_view").id, "form")
            ]
            action["res_id"] = productions.id
        return action

    # END #########
