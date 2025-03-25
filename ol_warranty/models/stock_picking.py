# Import Odoo libs
from odoo import fields, models
from datetime import timedelta


class StockPicking(models.Model):
    """Add methods for setting warranty fields on Serial/Lot."""

    _inherit = "stock.picking"

    # METHODS ###

    def _get_longest_warranty_period(self, product):
        warranty_periods = []
        for attribute_value in product.product_template_variant_value_ids:
            if (
                attribute_value.product_id
                and attribute_value.product_id.type == "service"
            ):
                warranty_period = attribute_value.product_id.warranty_period
                if warranty_period:
                    warranty_periods.append(int(warranty_period))
        return max(warranty_periods) if warranty_periods else 0

    def button_validate(self):
        res = super().button_validate()
        for move in self.move_ids:
            product = move.product_id
            longest_warranty_period = self._get_longest_warranty_period(product)
            if longest_warranty_period > 0:
                for move_line in move.move_line_ids:
                    if move_line.lot_id:
                        expiration_date = fields.Date.from_string(
                            self.scheduled_date
                        ) + timedelta(days=longest_warranty_period * 365)
                        move_line.lot_id.warranty_expiration_date = expiration_date
        return res

    # END #######
