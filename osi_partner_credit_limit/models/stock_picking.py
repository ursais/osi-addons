# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError
import datetime

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _compute_allow_transfer(self):
        for record in self:

            hold_value = False
            record.dont_allow_transfer = False
            # Only outgoing picking
            if record.picking_type_code == "outgoing" and record.state not in (
                "done",
                "cancel",
            ):
                # Sales person has a hold
                if (
                    record.sale_id.sales_hold
                    or record.sale_id.credit_hold
                    or record.sale_id.ship_hold
                ):
                    hold_value = True

                # Partner will exceed limit with current
                # Sale order or is over-due
                if record.sale_id.partner_id.check_limit(record.sale_id):
                    hold_value = True

                # Override applied on sale order
                if record.sale_id.credit_override:
                    hold_value = False

                record.dont_allow_transfer = hold_value
                record.sale_id.write({"ship_hold": hold_value})

    dont_allow_transfer = fields.Boolean(
        string="Hold Shipment", compute="_compute_allow_transfer"
    )
    ship_hold_days = fields.Integer(
        related="partner_id.parent_id.ship_hold_days",
        string="Customer Credit Period",
        help="Period past scheduled date for customer hold to verify credit card authorization",
    )
    customer_hold = fields.Boolean(
        "Customer Hold", help="On hold for credit card processing verification"
    )

    def button_validate(self):
        # Only outgoing picking
        if self.picking_type_code == "outgoing":
            if self.dont_allow_transfer:
                raise UserError(
                    _(
                        """Customer has a Credit hold.\n\nContact
                    Sales/Accounting to verify
                    sales hold/credit hold/overdue payments."""
                    )
                )
            elif self.customer_hold:
                raise UserError(
                    _(
                        "Customer probably has an expired credit authorization.\n\nContact\
                 Sales/Accounting to reprocess credit card."
                    )
                )
            else:
                return super(StockPicking, self).button_validate()

        # Incoming shipments / internal transfers
        else:
            return super(StockPicking, self).button_validate()

    def compute_customer_hold(self):
        # Only outgoing picking
        for picking in self:
            if picking.picking_type_code == "outgoing" and picking.state in (
                "assigned",
                "confirmed",
                "waiting",
            ):
                # check for customer hold
                if picking.ship_hold_days and (
                    datetime.timedelta(picking.ship_hold_days) + picking.scheduled_date
                    < datetime.datetime.now()
                ):
                    picking.customer_hold = True
                else:
                    picking.customer_hold = False
