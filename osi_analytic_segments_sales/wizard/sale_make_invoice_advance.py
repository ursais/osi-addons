# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)

        # Update Analytic account and Analytic Segments in Sale Order Line
        so_line.analytic_account_id = order.analytic_account_id.id
        so_line.analytic_segment_one_id = order.analytic_segment_one_id.id
        so_line.analytic_segment_two_id = order.analytic_segment_two_id.id

        return invoice
