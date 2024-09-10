# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # COLUMNS #####

    blind_ship_from = fields.Many2one(comodel_name="res.partner", string="Ship From")
    blind_drop_ship_csv = fields.Boolean(
        string="Blind Drop Ship Imported",
        help="""The imported value of "Blind Drop Ship".
        This overrides the calculated blind_drop_ship field.""",
    )
    csv_import = fields.Boolean(string="Imported From CSV")
    csv_customer_po = fields.Char(string="CSV Customer PO")
    csv_partner_shipping_id = fields.Many2one(
        comodel_name="res.partner", string="CSV Delivery Address", readonly=True
    )

    # END #########
    # METHODS #####

    @api.depends("sale_id", "blind_drop_ship_csv")
    def _compute_blind_drop_ship(self):
        """
        Override the value if the Picking was imported
        """
        res = super()._compute_blind_drop_ship()
        for picking in self:
            if picking.csv_import:
                # Use the imported value instead of the calculated one
                # if the picking was imported from a CSV file
                picking.blind_drop_ship = picking.blind_drop_ship_csv
        return res

    @api.constrains("blind_ship_from")
    def _check_blind_ship_from(self):
        """
        Check to make sure we only assign a value to this field on delivery orders.
        """
        for record in self:
            if record.blind_ship_from and record.picking_type_id.code != "outgoing":
                raise ValidationError(_('"Ship From" restricted to outgoing'))

    # END #########
