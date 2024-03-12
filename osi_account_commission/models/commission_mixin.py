# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class CommissionLineMixin(models.AbstractModel):
    _inherit = "commission.line.mixin"

    def _get_commission_amount(
        self, commission, subtotal, product, quantity, price_unit=0, discount=0
    ):
        """Get the commission amount for the data given. It's called by
        compute methods of children models.

        This means the inheritable method for modifying the amount of the commission.
        """
        self.ensure_one()
        if product.commission_free or not commission:
            return 0.0
        if commission.amount_base_type == "net_amount":
            # If subtotal (sale_price * quantity) is less than
            # standard_price * quantity, it means that we are selling at
            # lower price than we bought, so set amount_base to 0
            subtotal = max([0, subtotal - product.standard_price * quantity])
        if commission.commission_type == "fixed":
            if price_unit:
                return ((price_unit * quantity) - discount) * (
                    commission.fix_qty / 100.0
                )
            else:
                return subtotal * (commission.fix_qty / 100.0)
        elif commission.commission_type == "section":
            return commission.calculate_section(subtotal)
        elif commission.commission_type == "amount":
            return commission.amount
