# Import Odoo libs
from odoo import fields, models


class CRMLead(models.Model):
    """Add the ability to create Blanket Order's from Leads."""

    _inherit = "crm.lead"

    # COLUMNS ######

    blanket_order_ids = fields.One2many(
        comodel_name="sale.blanket.order",
        inverse_name="opportunity_id",
    )
    blanket_order_count = fields.Integer(
        string="Blanket Order Count",
        compute="_compute_blanket_order_count",
    )

    # END ##########
    # METHODS ##########

    def action_create_blanket_order(self):
        blanket_order_id = self.env["sale.blanket.order"].create(
            {
                "partner_id": self.partner_id.id,
                "pricelist_id": self.partner_id.property_product_pricelist.id,
                "company_id": self.company_id.id,
                "team_id": self.team_id.id,
                "payment_term_id": self.partner_id.property_payment_term_id.id,
                "opportunity_id": self.id,
                "carrier_id": self.partner_id.property_delivery_carrier_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.blanket.order",
            "view_mode": "form",
            "res_id": blanket_order_id.id,
            "target": "current",
        }

    def _compute_blanket_order_count(self):
        for lead in self:
            lead.blanket_order_count = len(lead.blanket_order_ids)

    def action_view_blanket_order(self):
        blanket_order_ids = self.blanket_order_ids
        action = self.env.ref("sale_blanket_order.act_open_blanket_order_view").read()[
            0
        ]
        ctx = {
            "default_partner_id": self.partner_id.id,
            "default_pricelist_id": self.partner_id.property_product_pricelist.id,
            "default_company_id": self.company_id.id,
            "default_team_id": self.team_id.id,
            "default_payment_term_id": self.partner_id.property_payment_term_id.id,
            "default_opportunity_id": self.id,
            "default_carrier_id": self.partner_id.property_delivery_carrier_id.id,
        }
        action.update({"context": ctx})
        if len(blanket_order_ids) == 1:
            action["views"] = [
                (
                    self.env.ref("sale_blanket_order.view_blanket_order_form").id,
                    "form",
                )
            ]
            action["res_id"] = blanket_order_ids.id
        else:
            action["domain"] = [("id", "in", blanket_order_ids.ids)]
        return action

    # END ##########
