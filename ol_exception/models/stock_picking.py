# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """
    Add sale_locked field to be used for order edit exceptions.
    Also adds new triggered field functionality to check exception if a
    triggered field is being updated.
    """

    _inherit = "stock.picking"

    # COLUMNS ######
    sale_locked = fields.Boolean(
        "Sale Order Locked",
        related="sale_id.locked",
    )

    # END ##########
    # METHODS ##########

    @api.constrains("ignore_exception", "move_ids", "state")
    def stock_check_exception(self):
        pickings = self.filtered(
            lambda s: s.state in ["waiting", "confirmed", "assigned"]
        )
        if pickings:
            pickings.with_context(raise_exception=False)._check_exception()

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

    # END ##########
