# Copyright (C) 2019 - 2023, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


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
        string="Credit Hold", compute="_compute_allow_transfer"
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
            else:
                return super(StockPicking, self).button_validate()

        # Incoming shipments / internal transfers
        else:
            return super(StockPicking, self).button_validate()
