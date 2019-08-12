from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    subscriptions = fields.Many2one(
        'sale.subscription',
        domain=[
            '|',
            ('stage_id', '=', 'In Progress'),
            ('stage_id', '=', 'Suspended')
        ]
    )

    partner_subscriptions = fields.Many2one(
        'sale.subscription'
    )

    single_partner = fields.Many2one(
        'res.partner'
    )

    # partner_credit_type = fields.Selection()
    # partner_credit_limit = fields.Float()
    # partner_credit = fields.Monetary()
    # service = fields.Many2one()

    # These functions are in agreement_sale_subscription_suspension
    # It's just not merged into osi-addons yet
    def suspend_service_profile(self):
        sp_ids = self.env['agreement.serviceprofile'].search([
            ('agreement_id', '=', self.agreement_id.id)])
        if sp_ids:
            sp_ids.write({'state': 'suspended'})

    def activate_service_profile(self):
        sp_ids = self.env['agreement.serviceprofile'].search([
            ('agreement_id', '=', self.agreement_id.id)])
        if sp_ids:
            sp_ids.write({'state': 'active'})

    def action_suspend(self):
        self.suspend_service_profile()
        return super().action_suspend()

    def action_re_activate(self):
        self.activate_service_profile()
        return super().action_re_activate()

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            stage_id = self.env['sale.subscription.stage'].search(
                [('id', '=', vals['stage_id'])])
            if stage_id.name == 'Suspended':
                self.suspend_service_profile()
            elif stage_id.name == "In Progress":
                self.activate_service_profile()
        return res
    # End unnecessary function duplication from Ken's unloaded module

    @api.model
    def check_service_suspensions(self, single_partner=None):
        # accepts opitonal passed partner_id to match subscriptions on
        # Doesn't it make more sense to base this off of subscription agreements?
        try:
            # if a specific partner record is passed, do an individual match
            if single_partner:
                _logger.info('Jacob passed a partner {}'.format(
                    single_partner)
                )
                self.partner_subscriptions = fields.Many2one(
                    'sale.subscription',
                    domain=[
                        ('partner_id', '=', single_partner)
                    ]
                )
                for sub in self.partner_subscriptions:
                    _logger.info('Jacob in for service-in-subscription loop')
                    # need to call Brian's function as a super
                    super(
                        SaleSubscription, self
                    ).sub.action_re_activate()
            # else default to processing/auditing all partner records
            else:
                _logger.info('Jacob did not pass a partner')
                # for all subscriptions, suspended or in progress
                for sub in self.subscriptions:
                    _logger.info('Jacob in for service-in-subscription loop 2')
                    _logger.info('Jacob partner matched {}'.format(
                        self.sub.partner_id)
                    )
                    # compute their credit and credit limit by credit type &
                    # compare the credit with their limit
                    # self.partner_credit_type = fields.Selection(
                    #     related='self.service.partner_id.credit_limit_type'
                    # )
                    # self.partner_credit_limit = fields.Float(
                    #     related='self.service.partner_id.credit_limit'
                    # )
                    # self.partner_credit = fields.Monetary(
                    #     related='self.service.partner_id.credit'
                    # )

                    if self.sub.partner_id.credit_limit_type == 'fixed':
                        _logger.info('Jacob partner credit type {}'.format(
                            self.sub.partner_id.credit_limit_type)
                        )
                        self.sub.partner_id = self.sub.partner_id
                        # if credit > credit limit or age > overdue limit then
                        # suspend all partner subscriptions
                        if self.sub.partner_id.credit > self.sub.partner_id.credit_limit:
                            super(
                                SaleSubscription, self
                            ).sub.action_suspend()
                        else:
                            super(
                                SaleSubscription, self
                            ).sub.action_re_activate()
                    elif self.sub.partner_id.credit_limit_type == 'subscription_based':
                        _logger.info('Jacob partner credit type {}'.format(
                            self.sub.partner_id.credit_limit_type)
                        )
                        # get the age of the oldest open invoice
                        # partner_credit_limit_subscription_qty = fields.Int(
                        #     related='partner.credit_limit_subscription_qty'
                        # )
                        # partner_credit_limit_subscription_uom = fields.Selection(
                        #     related='partner.credit_limit_subscription_uom'
                        # )
                        # if age > overdue limit then
                        # suspend all partner subscriptions
                        if self.age > self.overdue_limit:
                            super(
                                SaleSubscription, self
                            ).sub.action_suspend()
                        else:
                            super(
                                SaleSubscription, self
                            ).sub.action_re_activate()
                        # suspend or reactivate service as the case demands
        #  ~~~ Below is definitely WIP backup ~~~ #
        # elif self.partner.credit_limit_type == 'subscription_based':
        #     calculate the age of the oldest open invoice
        #     self.partner.credit_limit_subscription_qty
        #     self.partner.credit_limit_subscription_uom
        #     if self.age > self.overdue_limit:
        #         #Suspend all partner subscriptions
        #         super(
        #             checkServiceSuspensionState, self
        #         ).sub.action_suspend()
        #     else:
        #         super(
        #             checkServiceSuspensionState, self
        #         ).sub.action_re_activate()
        #     suspend or reactivate service as the case demands
        except RuntimeError as error:
            msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
            raise UserError(msg)
