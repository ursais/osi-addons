# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    authorize_acquirer = env.ref('payment.payment_acquirer_authorize')
    authorize_acquirer.write({
        'backend_confirm': 'authorize',
    })
