from odoo import models, fields
import math


class ProviderEconomy(models.Model):
    _inherit = "delivery.carrier"

    # COLUMNS ###
    delivery_type = fields.Selection(
        selection_add=[("economy", "Economy")],
        ondelete={"economy": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})},
    )
    economy_pound_or_less_price = fields.Float(
        string="Pound or Less Delivery Price", digits="Product Price", default=5.15
    )
    economy_more_than_a_pound_price = fields.Float(
        string="More than a Pound Delivery Price", digits="Product Price", default=15.30
    )
    economy_weight_unit = fields.Selection([('LBS', 'Pounds'), ('KGS', 'Kilograms')], default='LBS')

    # END COLUMNS ###

    def economy_rate_shipment(self, order):
        """
        Set the rate based on the weight in pounds
        """
        product_data = order.get_product_data_from_sale_order()
        product_total_weight = product_data.get("total_weight")
        total_weight_in_pounds = self._convert_weight(weight=product_total_weight, unit=self.economy_weight_unit)

        if total_weight_in_pounds <= 1:
            price = self.economy_pound_or_less_price
        else:
            price = self.economy_more_than_a_pound_price

        return {"success": True, "price": price, "error_message": False, "warning_message": False}
