from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_locked = fields.Boolean(
        "Sale Order Locked",
        related="sale_id.locked",
        store=True,
    )

    @api.constrains("ignore_exception", "move_ids", "state")
    def stock_check_exception(self):
        pickings = self.filtered(
            lambda s: s.state in ["waiting", "confirmed", "assigned"]
        )
        if pickings:
            pickings.with_context(check_exception=False)._check_exception()

    def _fields_trigger_check_exception(self):
        config_records = self.env["exception.config"].search(
            [("model_id.model", "=", "stock.picking")]
        )
        return [
            field.name
            for record in config_records
            for field in record.trigger_field_ids
        ]

    def _check_stock_check_exception(self, vals):
        check_exceptions = any(
            field in vals for field in self._fields_trigger_check_exception()
        )
        if check_exceptions:
            self.detect_exceptions()

    def write(self, vals):
        res = super().write(vals)
        self._check_stock_check_exception(vals)
        return res
