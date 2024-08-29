from odoo import api, fields, models


class StockPicking(models.Model):
    """Blind Dropship Functionality"""

    _inherit = "stock.picking"

    # COLUMNS #####
    # This field is stored and writable
    # so that its computed value can be overwritten by hand
    blind_drop_ship = fields.Boolean(
        string="Blind Drop Ship",
        compute="_compute_blind_drop_ship",
        store=True,
        readonly=False,
    )

    # END #########

    @api.depends("sale_id")
    def _compute_blind_drop_ship(self):
        """
        A picking is a blind drop shipment if its sale order contains
        the configured blind drop ship product.
        """
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("stock_move.blind_drop_ship")
        )

        # Get the Blind Drop ship Product
        blind_drop_ship_product_id = int(param) if param else None

        for picking in self:
            sale_lines = picking.sale_id.order_line
            line_products = sale_lines.product_id
            bom_products = sale_lines.bom_id.bom_line_ids.product_id

            picking.blind_drop_ship = (
                blind_drop_ship_product_id in line_products.ids
                or blind_drop_ship_product_id in bom_products.ids
            )
