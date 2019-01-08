# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agreement_template_id = fields.Many2one('agreement', string="Agreement Template", domain="[('is_template','=','True')]")
    agreement_id = fields.Many2one('agreement', string="Agreement")

    @api.multi
    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            if order.agreement_template_id:
                order.agreement_id = order.agreement_template_id.copy(default={
                    'name': order.name,
                    'is_template': False,
                    'sale_id': order.id,
                    'partner_id': order.partner_id.id,
                    'analytic_account_id': order.analytic_account_id,
                })
        return res
