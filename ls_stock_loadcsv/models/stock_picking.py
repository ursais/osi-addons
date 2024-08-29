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

    @api.model
    def create(self, vals):
        """
        Strip the dictionary of blind_ship_from value
        if type of transaction is anything other than outgoing.
        """
        picking_type_id = vals.get("picking_type_id")
        if picking_type_id:
            picking_type = self.env["stock.picking.type"].browse(picking_type_id)
            key = "blind_ship_from"
            if key in vals and picking_type.code != "outgoing":
                del vals[key]
        return super().create(vals)

    def _compute_client_order_ref(self):
        """
        Set client_order_ref from csv version if it exists.
        Overrides compute function defined in
        ls_delivery/models/stock_picking.py.
        """
        csv_pickings = self.filtered(lambda p: p.csv_customer_po)
        normal_pickings = self - csv_pickings

        for picking in csv_pickings:
            picking.client_order_ref = picking.csv_customer_po

        return super(StockPicking, normal_pickings)._compute_client_order_ref()

    @api.depends("partner_id")
    def _compute_shipping_id(self):
        """
        Set partner_shipping_id for csv orders. Overrides compute function defined in
        ls_delivery/models/stock_picking.py.
        """
        # pickings which have no sale order and are outgoing
        csv_pickings = self.filtered(
            lambda p: p.csv_import
            or (not p.sale_id and p.picking_type_id.code == "outgoing")
        )
        normal_pickings = self - csv_pickings

        for picking in csv_pickings:
            # If partner_shipping_id was already set on CSV
            # import in wizard/csv_loader_wizard.py,
            # don't override it
            if picking.csv_partner_shipping_id:
                picking.partner_shipping_id = picking.csv_partner_shipping_id
            else:
                picking.partner_shipping_id = picking.partner_id

        return super(StockPicking, normal_pickings)._compute_shipping_id()
