# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        res = super(SaleOrder, self)._onchange_partner_id_warning()

        partners = []
        for line in self.order_line:
            if line.product_id:
                # Partner Parent Child Record Can Show now
                partners.append(self.partner_id.id)
                if self.partner_id:
                    if self.partner_id.child_ids:
                        partners.extend(
                            child.id for child in self.partner_id.child_ids)
                    if self.partner_id.parent_id:
                        partners.append(self.partner_id.parent_id.id)
                        if self.partner_id.parent_id.child_ids:
                            partners.extend(
                                child.id for child in self.partner_id.parent_id.child_ids)
                customer_code = self.env['sh.product.customer.info'].sudo().search(
                    [('name', 'in', partners), '|', ('product_id', '=', line.product_id.id), ('product_tmpl_id', '=', line.product_id.id)],  order='id desc', limit=1)

                line.sh_line_customer_code = customer_code.product_code if customer_code and customer_code.product_code else False
                line.sh_line_customer_product_name = customer_code.product_name if customer_code and customer_code.product_name else False

                if line.product_id and customer_code:
                    des = " "

                    if customer_code.product_code:
                        des += f"[{customer_code.product_code}]"
                    if customer_code.product_name:
                        des += customer_code.product_name
                    line.name = des
                else:
                    line.name = line.product_id.display_name
        return res
