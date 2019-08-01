# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _


class checkServiceSuspensionState(models.Model):
    _inherit = 'sale.subscription'
    # inherit = 'ir.cron'

    passed_partner = fields.Char()

    passed_partner_id = fields.Integer()

    partner_subscriptions = fields.Many2one(
        'sale.subscription',
        domain=[
            ('partner_id', '=', passed_partner)
        ]
    )

    subscriptions = fields.Many2one(
        'sale.subscription',
        domain=[
            '|',
            ('stage_id', '=', 'In Progress'),
            ('stage_id', '=', 'Suspended')
        ]
    )

    subscription_partner = fields.Many2one(
        'res.partner',
        domain=[
            ('id', '=', passed_partner_id)
        ]
    )

    @api.multi
    def _check_service_suspensions(self, partner=None):
        try:
            # if a specific partner record is passed, do individual match
            if partner:
                self.passed_partner = partner
                for service in self.partner_subscriptions:
                    # need to call Brian's function as a super
                    super(checkServiceSuspensionState, self).service.action_re_activate()
            # else default to processing all partner records
            else:
                # gather all valid, active subscriptions
                for service in self.subscriptions:
                    # compute their credit and credit limit by credit type &
                    # compare the credit with their limit
                    if self.partner.credit_limit_type == 'fixed':
                        self.passed_partner_id = service.partner_id
                        # if credit > credit limit or age > overdue limit then
                        # suspend all partner subscriptions
                        if self.partner.credit > self.partner.credit_limit:
                            super(checkServiceSuspensionState, self).service.action_suspend()
                        else:
                            super(checkServiceSuspensionState, self).service.action_re_activate()
                    elif self.partner.credit_limit_type == 'subscription_based':
                        # get the age of the oldest open invoice
                        self.partner.credit_limit_subscription_qty
                        self.partner.credit_limit_subscription_uom
                        if self.age > self.overdue_limit:
                            # Suspend all partner subscriptions
                            super(checkServiceSuspensionState, self).service.action_suspend()
                        else:
                            super(checkServiceSuspensionState, self).service.action_re_activate()
                    # suspend or reactivate service as the case demands
        except RuntimeError as error:
            msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
            raise UserError(msg)
