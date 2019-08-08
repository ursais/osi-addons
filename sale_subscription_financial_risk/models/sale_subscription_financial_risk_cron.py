from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _


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

    @api.model
    def check_service_suspensions(self, partner=None):
        try:
            # if a specific partner record is passed, do individual match
            if partner:
                self.passed_partner = partner
                partner_subscriptions = fields.Many2one(
                    'sale.subscription',
                    domain=[
                        ('partner_id', '=', partner)
                    ]
                )
                for service in partner_subscriptions:
                    # need to call Brian's function as a super
                    super(
                        SaleSubscription, self
                    ).service.action_re_activate()
            # else default to processing all partner records
            else:
                # I think it is angry about using subscriptions in this manner
                # gather all valid, active subscriptions
                for service in self.subscriptions:
                    # compute their credit and credit limit by credit type &
                    # compare the credit with their limit
                    partner = fields.Many2one(
                        'res.partner',
                        domain=[
                            ('id', '=', service.partner_id)
                        ]
                    )

                    partner_credit_type = fields.Selection(
                        related='partner.credit_limit_type'
                    )
                    partner_credit_limit = fields.Float(
                        related='partner.credit_limit'
                    )
                    partner_credit = fields.Monetary(
                        related='partner.credit'
                    )

                    if partner_credit_type == 'fixed':
                        self.passed_partner_id = service.partner_id
                        # if credit > credit limit or age > overdue limit then
                        # suspend all partner subscriptions
                        if partner_credit > partner_credit_limit:
                            super(
                                SaleSubscription, self
                            ).service.action_suspend()
                        else:
                            super(
                                SaleSubscription, self
                            ).service.action_re_activate()
                    elif partner_credit_type == 'subscription_based':
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
                            ).service.action_suspend()
                        else:
                            super(
                                SaleSubscription, self
                            ).service.action_re_activate()
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
        #         ).service.action_suspend()
        #     else:
        #         super(
        #             checkServiceSuspensionState, self
        #         ).service.action_re_activate()
        #     suspend or reactivate service as the case demands
        except RuntimeError as error:
            msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
            raise UserError(msg)
