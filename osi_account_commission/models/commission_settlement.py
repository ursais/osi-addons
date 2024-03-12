# Copyright 2023 Open Source Integrators Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class CommissionSettlement(models.Model):
    _inherit = "commission.settlement"

    settlement_type = fields.Selection(
        selection_add=[("sale_invoice", "Sales Invoices")],
        ondelete={"sale_invoice": "set default"},
    )
    state = fields.Selection(
        selection_add=[
            ("paid", "Paid"),
        ],
        ondelete={"paid": "set default"},
    )

    def action_paid(self):
        """Mark selected settlements as paid."""
        settlements = self.filtered(lambda x: x.state in ("settled", "invoiced"))
        if settlements:
            settlements.write({"state": "paid"})

    def unlink(self):
        """Allow to delete only cancelled settlements."""
        if any(x.state in ("invoiced", "paid") for x in self):
            raise UserError(_("You can't delete invoiced or paid settlements."))
        return super().unlink()

    def action_invoice(self):
        raise UserError(_("Payments happen through Payroll. You can't invoice here."))
