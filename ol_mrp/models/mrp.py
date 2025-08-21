# Import Odoo libs
from odoo import fields, models


class MrpProduction(models.Model):
    """
    Add functions for printing MO based reports and add sale tags
    """

    _inherit = "mrp.production"

    # COLUMNS #####

    tag_ids = fields.Many2many(
        related="sale_order_id.tag_ids",
        string="Tags",
        store=False,
    )

    # END #########
    # METHODS ##########

    def get_bin_label_data(self):
        """
        Get a dict of information for this MO to be used on the bin label
        """
        self.ensure_one()

        res = {
            "name": self.name,
            "product": f"{self.product_qty}x {self.product_id.default_code}",
            "sale_order": "",
            "rush_order": False,
            "customer": "",
            "salesperson": "",
            "carrier": "",
            "ship_by": "",
        }

        sale_orders = (
            self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id
        )
        sale_order_id = sale_orders and sale_orders[0] or False
        if sale_order_id:
            res.update(
                {
                    "sale_order": sale_order_id.name,
                    "rush_order": sale_order_id.rush_order,
                    "customer": sale_order_id.partner_id.company_name
                    or sale_order_id.partner_id.commercial_company_name,
                    "salesperson": sale_order_id.user_id.name,
                    "carrier": sale_order_id.carrier_id.name,
                    "ship_by": sale_order_id.original_commitment_date,
                }
            )
        return res

    def button_scrap(self):
        action = super().button_scrap()
        ctx = action.get("context")
        ctx.update({"default_should_replenish": True})
        action["context"] = ctx
        return action

    # END #########
