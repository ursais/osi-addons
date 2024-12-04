from odoo import fields, models


class MrpProduction(models.Model):
    """
    Adding fields to Manufacturing Order.
    """

    _inherit = "mrp.production"

    # COLUMNS ##########

    rush_order = fields.Boolean(
        "Rush Order",
        related="procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.rush_order",
        readonly=False,
        tracking=True,
    )
    rush_order_sale_id = fields.Many2one(
        related="procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id"
    )

    # END ##########
    # METHODS #########

    def write(self, vals):
        result = super().write(vals)
        # If setting the rush order in the MO, then set the rush_order_manual
        # field on the sale order.
        if "rush_order" in vals:
            for record in self:
                sale_order = record.rush_order_sale_id
                if sale_order and not sale_order.rush_order_manual:
                    sale_order.rush_order = vals["rush_order"]
        return result

    # END ##########
