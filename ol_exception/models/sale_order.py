from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _fields_trigger_check_exception(self):
        config_records = self.env["exception.config"].search(
            [("model_id.model", "=", "sale.order")]
        )
        return [
            field.name
            for record in config_records
            for field in record.trigger_field_ids
        ]

    def write(self, vals):
        """Since Stock Pickings & Manufacturing Orders have a related
        field to the locked field, changing it doesn't flow through write
        method therfore we have to trick it here passing through vals."""
        res = super(SaleOrder, self).write(vals)
        if "locked" in vals:
            pickings = self.env["stock.picking"].search([("sale_id", "in", self.ids)])
            pickings._check_stock_check_exception({"sale_locked": vals["locked"]})
            mrp_productions = self.env["mrp.production"].search(
                [("sale_order_id", "in", self.ids)]
            )
            mrp_productions._check_mrp_check_exception({"sale_locked": vals["locked"]})
        return res
