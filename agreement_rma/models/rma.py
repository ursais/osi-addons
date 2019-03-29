# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RMAOrderLine(models.Model):
    _inherit = "rma.order.line"

    agreement_id = fields.Many2one('agreement', 'Agreement')
    serviceprofile_id = fields.Many2one('agreement.serviceprofile',
                                        'Service Profile')

    @api.onchange('partner_id')
    def _onchange_partner(self):
        self.agreement_id = False

    @api.onchange('agreement_id')
    def _onchange_agreement(self):
        self.serviceprofile_id = False
