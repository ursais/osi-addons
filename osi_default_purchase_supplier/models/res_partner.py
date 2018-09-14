# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    generic_flag = fields.Boolean(string="Generic", default=False)

    @api.model
    def create(self, vals):
        if vals.get('generic_flag'):
            generic_flag = self.search([('generic_flag', '=', True)])
            if generic_flag:
                raise UserError(_(
                    "You can not create partner with generic = True because "
                    "we already have one generic supplier."))
        return super(ResPartner, self).create(vals=vals)

    @api.multi
    def write(self, vals):
        if vals.get('generic_flag'):
            generic_flag = self.search([('generic_flag', '=', True)])
            if generic_flag:
                raise UserError(_(
                    "You can not create partner with generic = True because "
                    "we already have one generic supplier."))
        return super(ResPartner, self).write(vals=vals)
