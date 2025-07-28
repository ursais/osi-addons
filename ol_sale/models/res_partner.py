# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add new field to Partners."""

    _inherit = "res.partner"

    # COLUMNS #####

    account_manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Account Manager",
    )
    sale_order_tag_ids = fields.Many2many(
        comodel_name="crm.tag",
        relation="res_partner_tag_rel",
        column1="partner_id",
        column2="tag_id",
        string="Sale Order Tags",
    )
    delivery_order_count = fields.Integer(
        string="Delivery Orders",
        compute="_compute_delivery_order_count",
    )

    # END #########
    # METHODS #####

    def _compute_delivery_order_count(self):
        for partner in self:
            partner_ids = partner._get_partner_and_children_ids()
            count = self.env["stock.picking"].search_count(
                [
                    ("partner_id", "in", partner_ids),
                    ("picking_type_id.code", "=", "outgoing"),
                ]
            )
            partner.delivery_order_count = count

    def _get_partner_and_children_ids(self):
        return self.with_context(active_test=False).child_ids.ids + [self.id]

    def action_view_delivery_orders(self):
        self.ensure_one()
        partner_ids = self._get_partner_and_children_ids()
        return {
            "type": "ir.actions.act_window",
            "name": "Delivery Orders",
            "view_mode": "tree,form",
            "res_model": "stock.picking",
            "domain": [
                ("partner_id", "in", partner_ids),
                ("picking_type_id.code", "=", "outgoing"),
            ],
            "context": dict(self.env.context, default_partner_id=self.id),
        }

    # END #########
