from odoo import models, fields, api
from datetime import date, datetime, timedelta
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

    to_suspend = fields.Boolean(default=False)

    partner_invoices = fields.Date(
        'account.invoice'
    )

    # ~~These functions are in agreement_sale_subscription_suspension Ken did
    # ~~It's just not merged into osi-addons yet

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

    # ~~End unnecessary function duplication from Ken's unloaded module~~ #

    def _get_delta_qty(self, limit_qty, limit_uom):
        if limit_uom == 'days':
            delta_qty = timedelta(days=limit_qty)
        elif limit_uom == 'weeks':
            delta_qty = timedelta(weeks=limit_qty)
        elif limit_uom == 'months':
            delta_qty = timedelta(months=limit_qty)
        return delta_qty

    def _get_delta_mod(self, subscription_qty, subscription_uom):
        if subscription_uom == 'weeks':
            delta_mod = timedelta(weeks=subscription_qty)
        elif subscription_uom == 'months':
            delta_mod = timedelta(months=subscription_qty)
        elif subscription_uom == 'quarters':
            delta_mod = timedelta(months=(3 * subscription_qty))
        elif subscription_uom == 'years':
            delta_mod = timedelta(years=subscription_qty)
        return delta_mod

    # The calling cron job controls looping through all model records
    # during function call
    @api.model
    def check_service_suspensions(self):
        for subscription_id in self:
            try:
                _logger.info('Jacob starting suspension check batch')
                # get the age of the oldest open invoice
                oldest_invoice = subscription_id.env['account.invoice'].search(
                    [
                        ('partner_id', '=', subscription_id.partner_id.id),
                        ('state', '=', 'open')
                    ],
                    order="date_due asc"
                )
                _logger.info('Jacob grabbed oldest invoice for contact {}'.format(
                    subscription_id.partner_id.name
                ))
                if oldest_invoice:
                    _logger.info('Jacob grabbed oldest invoice date_due is {}'.format(
                        oldest_invoice[0].date_due
                    ))
                    # compute their credit and their credit limit based on type
                    if subscription_id.partner_id.credit_limit_type == 'fixed':
                        cur_date = date.today()
                        # this is ugly and needs to be fixed, but I can't directly
                        # insert self.partner_id.overdue_limit_uom in the timedelta call
                        # as a keyword

                        # Calculate the delta_qty allowable for aging invoices
                        delta_qty = subscription_id._get_delta_qty(
                            subscription_id.partner_id.overdue_limit_qty,
                            subscription_id.partner_id.overdue_limit_uom
                        )

                        _logger.info('Jacob time_now is {}'.format(
                            cur_date)
                        )
                        _logger.info('Jacob delta_qty is {}'.format(
                            delta_qty)
                        )
                        _logger.info('Jacob partner credit type {}'.format(
                            subscription_id.partner_id.credit_limit_type)
                        )

                        # format the credit float to prevent precision error
                        formatted_credit = format(subscription_id.partner_id.credit, '.2f')

                        # Check for suspension by credit limit
                        if float(formatted_credit) > subscription_id.\
                                partner_id.credit_limit:
                            _logger.info('Jacob suspending case 1!')
                            _logger.info('Jacob self.partner_id.credit {} !'.format(
                                subscription_id.partner_id.credit
                            ))
                            _logger.info('Jacob formatted_credit {} !'.format(
                                formatted_credit
                            ))
                            _logger.info('Jacob self.partner_id.credit_limit {} !'.format(
                                subscription_id.partner_id.credit_limit
                            ))
                            subscription_id.action_suspend()
                        # Check for suspension by invoice age
                        elif oldest_invoice[0].date_due + delta_qty < cur_date:
                            _logger.info('Jacob oldest_invoice[0].date_due {} !'.format(
                                oldest_invoice[0].date_due
                            ))
                            _logger.info('Jacob oldest_invoice[0].date_due + delta_qty {} !'.format(
                                (oldest_invoice[0].date_due + delta_qty)
                            ))
                            _logger.info('Jacob cur_date {} !'.format(
                                cur_date
                            ))
                            _logger.info('Jacob suspending case 2!')
                            subscription_id.action_suspend()
                        else:
                            _logger.info('Jacob activating!')
                            subscription_id.action_re_activate()

                    # Same thing, but for subscription-based credit limits
                    # I need a little clarification on calculating this - Max
                    elif subscription_id.partner_id.credit_limit_type == \
                            'subscription_based':
                        cur_date = date.today()
                        _logger.info('Jacob partner credit type {}'.format(
                            subscription_id.partner_id.credit_limit_type)
                        )

                        # Calculate the delta_qty allowable for aging invoices
                        delta_qty = subscription_id._get_delta_qty(
                            subscription_id.partner_id.overdue_limit_qty,
                            subscription_id.partner_id.overdue_limit_uom
                        )

                        _logger.info('Jacob time_now is {}'.format(
                            cur_date)
                        )
                        _logger.info('Jacob delta_qty is {}'.format(
                            delta_qty)
                        )

                        # calculate credit using credit_limit_subscription_qty
                        delta_mod = subscription_id._get_delta_mod(
                            subscription_id.partner_id.credit_limit_subscription_qty,
                            subscription_id.partner_id.credit_limit_subscription_uom
                        )

                        _logger.info('Jacob delta_mod is {}'.format(
                            delta_mod)
                        )
                        delta_qty = delta_qty + delta_mod
                        _logger.info('Jacob final delta_qty is {}'.format(
                            delta_qty)
                        )

                        # Check for suspension by invoice age
                        if oldest_invoice[0].date_due + delta_qty < cur_date:
                            _logger.info('Jacob oldest_invoice[0].date_due {} !'.format(
                                oldest_invoice[0].date_due
                            ))
                            _logger.info('Jacob oldest_invoice[0].date_due + delta_qty {} !'.format(
                                (oldest_invoice[0].date_due + delta_qty)
                            ))
                            _logger.info('Jacob cur_date {} !'.format(
                                cur_date
                            ))
                            _logger.info('Jacob suspending!')
                            subscription_id.action_suspend()
                        else:
                            _logger.info('Jacob activating!')
                            subscription_id.action_re_activate()

            except RuntimeError as error:
                msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
                raise UserError(msg)
