# Import Odoo libs
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # COLUMNS #####
    lithium_shipping_hazard = fields.Boolean(
        string="Lithium Shipping Hazard",
        compute="_compute_lithium_shipping_hazard",
        readonly=True,
        store=True,
    )
    delivery_account_number = fields.Char(
        string="Shipping Account",
        compute="_compute_delivery_account_number",
        readonly=True,
        store=True,
    )
    delivery_notes = fields.Text(
        string="Delivery Note",
        related="sale_id.delivery_notes",
    )

    # END #########

    @api.depends("move_ids.product_id.lithium_shipping_hazard")
    def _compute_lithium_shipping_hazard(self):
        """
        A picking has lithium shipping hazard any product is flagged as lithium shipping hazard

        NOTE: This function does not attempt to take phantom kits into account. The phantom kit
              product should be marked with lithium hazard if it contains hazardous materials.
        """
        for picking in self:
            if any(picking.mapped("move_ids.product_id.lithium_shipping_hazard")):
                picking.lithium_shipping_hazard = True
            else:
                picking.lithium_shipping_hazard = False

    @api.depends("group_id.sale_id.delivery_account_number")
    def _compute_delivery_account_number(self):
        """
        Compute the delivery account number
        This is computed instead of related so that later modules can extend it
        """
        for picking in self:
            picking.delivery_account_number = (
                picking.group_id.sale_id.delivery_account_number
            )
