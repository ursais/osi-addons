# Import Odoo libs
from odoo import api, fields, models


class MRPProduction(models.Model):
    """
    Add sale_locked field to be used for order edit exceptions.
    Also adds new triggered field functionality to check exception if a
    triggered field is being updated.
    """

    _inherit = "mrp.production"

    # COLUMNS ######

    sale_locked = fields.Boolean(
        "Sale Order Locked",
        related="sale_order_id.locked",
    )

    # END ##########
    # METHODS ##########

    @api.constrains("ignore_exception", "move_raw_ids", "product_id")
    def mrp_check_exception(self):
        mrp_orders = self.filtered(
            lambda s: s.state in ["confirmed", "progress", "to_close"]
        )
        if mrp_orders:
            mrp_orders.with_context(raise_exception=False)._check_exception()

    def _fields_trigger_check_exception(self):
        # Search for exception configs: sudo is used as non-admins don't
        # have direct access to ir.model
        config_records = (
            self.env["exception.config"]
            .sudo()
            .search([("model_id.model", "=", self._name)])
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

    def button_mark_done(self):
        for rec in self:
            if rec.detect_exceptions() and not rec.ignore_exception:
                return rec._popup_exceptions()
        return super(MRPProduction, self).button_mark_done()

    # END ##########
