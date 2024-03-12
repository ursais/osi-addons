# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("line_ids.product_id.commission_id", "line_ids.agent_ids.amount")
    def _compute_commission_total(self):
        for record in self:
            record.commission_total = 0.0
            for line in record.line_ids:
                commission = line.product_id.commission_id
                if commission:
                    if commission.commission_type == "amount":
                        record.commission_total += commission.amount
                    elif commission.commission_type == "fixed":
                        record.commission_total += (
                            (line.price_unit * line.quantity) - line.discount
                        ) * (commission.fix_qty / 100.0)
                    elif commission.commission_type == "section":
                        record.commission_total += commission.calculate_section(
                            line.price_subtotal
                        )
                else:
                    record.commission_total += sum(x.amount for x in line.agent_ids)


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    @api.depends(
        "object_id.price_subtotal",
        "object_id.commission_free",
        "commission_id",
    )
    def _compute_amount(self):
        for line in self:
            inv_line = line.object_id
            commission_id = (
                inv_line.product_id.commission_id
                if inv_line.product_id.commission_id
                else line.commission_id
            )
            line.amount = line._get_commission_amount(
                commission_id,
                inv_line.price_subtotal,
                inv_line.product_id,
                inv_line.quantity,
                price_unit=inv_line.price_unit,
                discount=inv_line.discount,
            )
            # Refunds commisslineions are negative
            if line.invoice_id.move_type and "refund" in line.invoice_id.move_type:
                line.amount = -line.amount
