# Copyright (C) 2019 - 2023, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sales_hold = fields.Boolean(
        related="partner_id.sales_hold", string="Customer Sales Hold"
    )
    credit_hold = fields.Boolean(
        related="partner_id.credit_hold", string="Customer Credit Hold"
    )
    ship_hold = fields.Boolean(string="Delivery Hold", copy=False)
    credit_override = fields.Boolean(
        string="Override Hold", tracking=True, default=False
    )

    osi_partner_credit_warning = fields.Text(
        compute='_compute_osi_partner_credit_warning')

    @api.depends('partner_id',)
    def _compute_osi_partner_credit_warning(self):
        # Show the Warning banner with the credit available for user when drafting a new SO
        for order in self:
            order.partner_credit_warning = ''
            show_warning = order.state in ('draft', 'sent') and \
                           order.partner_id.osi_credit_limit
            if show_warning:
                order.osi_partner_credit_warning = "{} has only {} credit available".format(
                    order.partner_id.display_name,
                    order.partner_id.osi_credit_limit - order.partner_id.used_credit_limit_balance())

    def action_confirm(self):
        self.partner_id.with_context(from_sale_order=True).check_limit(self)
        if self.sales_hold and not self.credit_override:
            message = _("""Cannot confirm Order! The customer is on sales hold.""")
            # Display that the customer is on sales hold
            raise ValidationError(message)
        elif self.ship_hold and not self.credit_override:
            message = _(
                """Cannot confirm Order! \nThe customer exceed available credit limit and is on ship hold."""
            )
            raise ValidationError(message)
        else:
            # attempt to change the state of this order to be included in \
            #  the computation for check_limit function
            prev_state = self.state
            self.state = "sale"
            if (
                self.partner_id.with_context(from_sale_order=True).check_limit(self)
                and not self.credit_override
            ):
                self.state = prev_state
                self.ship_hold = True
                message = _(
                    """Cannot confirm Order! \nThis will exceed allowed Credit Limit.
                    \nTo Override, check Override Sales/Credit/Delivery Hold"""
                )
                raise ValidationError(message)
            return super(SaleOrder, self).action_confirm()
