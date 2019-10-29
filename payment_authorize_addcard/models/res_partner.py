# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, api, _
from odoo.exceptions import UserError
from werkzeug import url_encode


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def validate_partner(self):
        self.ensure_one()
        fields = []
        if not self.street:
            fields.append('Street')
        if not self.zip:
            fields.append('Zip')
        if not self.city:
            fields.append('City')
        if fields:
            raise UserError(
                _("Customer doesn't have the following \n%s" % '\n'.join(fields)))

    @api.multi
    def payment_url(self):
        self.ensure_one()
        self.validate_partner()
        values_to_pass = dict(self._context.get('params', {}))
        values_to_pass.update({
            'model': self._name,
            'id': self.id,
        })
        final_url = "user/payment_method/%s/?%s" % (
            self.id, url_encode(values_to_pass))
        return {
            'type': 'ir.actions.act_url',
            'url': final_url,
            'nodestroy': True,
            'target': 'self'
        }
