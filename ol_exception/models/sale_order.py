# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """
    Also adds new triggered field functionality to check exception if a
    triggered field is being updated.
    """

    _inherit = "sale.order"

    # METHODS ##########

    def sale_check_exception(self):
        sale_orders = self.filtered(lambda s: s.state in ["sent", "sale"])
        if sale_orders:
            sale_orders.with_context(raise_exception=False)._check_exception()

    def action_quotation_send(self):
        # Trigger exception check when attempting to send email
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().action_quotation_send()

    def action_lock(self):
        # Trigger exception check when attempting to lock the order.
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().action_lock()

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

    def write(self, vals):
        trigger_fields = self._fields_trigger_check_exception()
        relevant_changes = {
            field: vals[field] for field in trigger_fields if field in vals
        }

        # Get field mappings from exception.config: sudo is used as non-admins don't
        # have direct access to ir.model
        config_records = (
            self.env["exception.config"]
            .sudo()
            .search([("model_id.model", "=", "sale.order")])
        )
        field_mapping = {}
        for config in config_records:
            mapping = config.get_field_mapping()
            field_mapping.update(mapping)

        # Map changes to related fields
        related_changes = {}
        for field, value in relevant_changes.items():
            if field in field_mapping:
                for related_field in field_mapping[field]:
                    related_changes[related_field] = value

        # Call super to apply the write
        res = super().write(vals)

        # Handle exception checks for related fields
        if related_changes:
            pickings = self.env["stock.picking"].search([("sale_id", "in", self.ids)])
            pickings._check_stock_check_exception(related_changes)

            mrp_productions = self.env["mrp.production"].search(
                [("sale_order_id", "in", self.ids)]
            )
            mrp_productions._check_mrp_check_exception(related_changes)

        return res

    # END ##########
