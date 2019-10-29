# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import http
from odoo.http import request
from werkzeug import utils, url_encode
from odoo.addons.payment_authorize.controllers.main import AuthorizeController


class WebsitePayment(AuthorizeController):

    @http.route(
        ["/user/payment_method/<model('res.partner'):partner>"],
        type='http',
        auth="user",
        methods=['GET'],
        website=True)
    def payment_method_input(self, partner, **kwargs):
        acquirers = request.env['payment.acquirer'].search(
            [('website_published', '=', True),
             ('registration_view_template_id', '!=', False),
             ('payment_flow', '=', 's2s')]
        )
        payment_tokens = partner.payment_token_ids
        payment_tokens |= partner.commercial_partner_id.sudo().payment_token_ids
        action_id = kwargs.get('action', False)
        if kwargs.get('model', False) in [
                'sale.order', 'account.invoice', 'res.partner']:
            request.env[kwargs.get('model')].browse(
                int(kwargs.get('id')))
            if kwargs.get('model', False) == 'sale.order':
                action_xml_id = 'sale.action_orders'
                if payment_tokens:
                    sale_id = int(kwargs.get('id'))
                    order = request.env['sale.order'].sudo().browse(sale_id)
                    order['payment_token_id'] = payment_tokens[0]
            elif kwargs.get('model', False) == 'account.invoice':
                action_xml_id = 'account.action_invoice_tree1'
                if payment_tokens:
                    invoice_id = int(kwargs.get('id'))
                    invoice = request.env[
                        'account.invoice'].sudo().browse(invoice_id)
                    invoice['payment_token_id'] = payment_tokens[0]
            elif kwargs.get('model', False) == 'res.partner':
                action_xml_id = 'base.action_partner_form'
            action_id = request.env.ref(action_xml_id).id
            kwargs.update({
                'action': action_id,
            })

        return_url = request.params.get(
            'redirect', '/user/payment_method/%s/?%s' %
            (partner.id, url_encode(dict(kwargs))))
        values = dict(kwargs)
        values.update({
            'pms': payment_tokens,
            'acquirers': acquirers,
            'return_url': return_url,
            'bootstrap_formatting': True,
            'partner_id': partner.id,
        })
        return request.render("payment_authorize_addcard.pay_methods", values)
