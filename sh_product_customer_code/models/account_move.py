# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if self._origin and self._origin.invoice_line_ids:
            partners = [self.partner_id.id]
            if self.partner_id:
                if self.partner_id.child_ids:
                    partners.extend(
                        child.id for child in self.partner_id.child_ids)
                if self.partner_id.parent_id:
                    partners.append(self.partner_id.parent_id.id)
                    if self.partner_id.parent_id.child_ids:
                        partners.extend(
                            child.id for child in self.partner_id.parent_id.child_ids)

            for line in self._origin.invoice_line_ids:
                customer_code = self.env['sh.product.customer.info'].sudo(
                ).search([('name', 'in', partners),
                          ('product_id', '=', line.product_id.id)],
                         limit=1)
                line.sh_line_customer_code = customer_code.product_code if customer_code and customer_code.product_code else False
                line.sh_line_customer_product_name = customer_code.product_name if customer_code and customer_code.product_name else False

        return res
