from odoo import api, fields, models


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    sale_locked = fields.Boolean(
        "Sale Order Locked",
        related="sale_order_id.locked",
        store=True,
    )

    @api.constrains("ignore_exception", "move_raw_ids", "product_id")
    def mrp_check_exception(self):
        mrp_orders = self.filtered(
            lambda s: s.state in ["draft", "confirmed", "progress", "to_close"]
        )
        if mrp_orders:
            mrp_orders.with_context(check_exception=False)._check_exception()

    def _fields_trigger_check_exception(self):
        config_records = self.env["exception.config"].search(
            [("model_id.model", "=", self._name)]
        )
        fields_to_check = set()
        for config in config_records:
            # Include directly configured fields
            fields_to_check.update(field.name for field in config.trigger_field_ids)
            # Include dynamically discovered related fields
            related_fields = config.get_related_fields()
            fields_to_check.update(field.name for field in related_fields)
        return list(fields_to_check)

    def _check_mrp_check_exception(self, vals):
        check_exceptions = any(
            field in vals for field in self._fields_trigger_check_exception()
        )
        if check_exceptions:
            self.detect_exceptions()

    def write(self, vals):
        res = super().write(vals)
        self._check_mrp_check_exception(vals)
        return res
