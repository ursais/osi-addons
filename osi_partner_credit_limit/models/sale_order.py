# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sales_hold = fields.Boolean(
        related="partner_id.sales_hold", string="Customer Sales Hold"
    )
    credit_hold = fields.Boolean(
        related="partner_id.credit_hold", string="Customer Credit Hold"
    )
    ship_hold = fields.Boolean(string="Order Sales/Ship Hold", copy=False)
    credit_override = fields.Boolean(
        string="Override Sales/Credit/Ship Hold", tracking=True, default=False
    )

    def action_confirm(self):
        state = self.partner_id.check_limit(self)
        if self.sales_hold and not self.credit_override:
            message = _(
                """Cannot confirm Order!The customer is on Customer Sales Hold."""
            )
            # Display that the customer is on sales hold
            raise ValidationError(message)
        elif self.ship_hold and not self.credit_override:
            message = _(
                """Cannot confirm Order! The customer is on Order Sales Hold."""
            )
            raise ValidationError(message)
        else:
            # attempt to change the state of this order to be included in \
            #  the computation for check_limit function
            prev_state = self.state
            self.state = "sale"
            if self.partner_id.check_limit(self) and not self.credit_override:
                self.state = prev_state
                self.ship_hold = True
                # commit changes above before ORM rollback any changes.
                self._cr.commit()
                message = _(
                    """Cannot confirm Order!
                        This will put Customer over Credit Limit.
                        To Override, check Override Sales/Credit/Ship Hold"""
                )
                raise ValidationError(message)

            return super(SaleOrder, self).action_confirm()
