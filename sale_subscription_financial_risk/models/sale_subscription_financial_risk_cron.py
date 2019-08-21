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
        for subscription_id in self:
            sp_ids = self.env['agreement.serviceprofile'].search([
                ('agreement_id', '=', subscription_id.agreement_id.id)])
            if sp_ids:
                sp_ids.write({'state': 'suspended'})

    def activate_service_profile(self):
        for subscription_id in self:
            sp_ids = self.env['agreement.serviceprofile'].search([
                ('agreement_id', '=', subscription_id.agreement_id.id)])
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

    # Calculates and returns a timedelta based on the customer's credit terms
    def _get_delta_qty(self, qty, uom):
        if uom == 'days':
            delta_qty = timedelta(days=qty)
        elif uom == 'weeks':
            delta_qty = timedelta(weeks=qty)
        elif uom == 'months':
            delta_qty = timedelta(months=qty)
        elif uom == 'quarters':
            delta_qty = timedelta(months=(3 * qty))
        elif uom == 'years':
            delta_qty = timedelta(years=qty)
        return delta_qty

    # May be called by an account.invoice onchange/payment received or
    # by the batch loop cron sale_subscription_financial_risk_suspend.xml
    @api.model
    def check_service_suspensions(self):
        for subscription_id in self:
            try:
                _logger.info('Jacob starting suspension check!')
                # get list of open invoices, sorted by oldest open
                open_invoices = subscription_id.env['account.invoice'].search(
                    [
                        ('partner_id', '=', subscription_id.partner_id.id),
                        ('state', '=', 'open')
                    ],
                    order="date_due asc"
                )
                _logger.info('Jacob grabbed oldest invoice for contact {}'.format(
                    subscription_id.partner_id.name
                ))
                if open_invoices:
                    _logger.info('Jacob grabbed oldest invoice date_due is {}'.format(
                        open_invoices[0].date_due
                    ))
                    # Compute their credit and their credit limit based on type
                    # Using the oldest open invoice
                    # Inspected fixed credit based limits
                    if subscription_id.partner_id.credit_limit_type == 'fixed':
                        cur_date = date.today()

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
                        formatted_credit = format(
                            subscription_id.partner_id.credit, '.2f'
                        )

                        # Check for violation by credit limit
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
                        # Check for violation by invoice age
                        elif open_invoices[0].date_due + delta_qty < cur_date:
                            _logger.info('Jacob open_invoices[0].date_due {} !'.format(
                                open_invoices[0].date_due
                            ))
                            _logger.info('Jacob open_invoices[0].date_due + delta_qty {} !'.format(
                                (open_invoices[0].date_due + delta_qty)
                            ))
                            _logger.info('Jacob cur_date {} !'.format(
                                cur_date
                            ))
                            _logger.info('Jacob suspending case 2!')
                            subscription_id.action_suspend()
                        # Otherwise, re-activate everything if suspended
                        elif subscription_id.stage_id.name == 'suspended':
                            _logger.info('Jacob activating!')
                            _logger.info('Jacob stage id is {}!'.format(subscription_id.stage_id.name))
                            subscription_id.action_re_activate()
                        # Default state print to confirm inspection for testng
                        else:
                            _logger.info('Jacob no action needed for customer')

                    # Inspecting subscription-based credit limits
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

                        # Determine delta modifier to define invoice range
                        delta_mod = subscription_id._get_delta_qty(
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

                        i = 0

                        # filter open_invoices list to valid subscription range
                        valid_invoices = filter(
                            lambda invoice:
                                invoice.date_due + delta_mod > cur_date,
                                open_invoices
                        )

                        # Bool to hold whether a partner is in violation or not
                        # use subscription_id.partner_id.risk_exception instead?
                        in_violation = False

                        # Check for violation for invoices in valid range
                        for invoice in valid_invoices:
                            # if the invoice is in violation, suspend
                            if invoice.date_due + delta_qty < cur_date:
                                _logger.info('Jacob open_invoices[{}].date_due {} !'.format(i, open_invoices[i].date_due))
                                _logger.info('Jacob open_invoices[{}].date_due + delta_qty {} !'.format(i, (open_invoices[i].date_due + delta_qty)))
                                _logger.info('Jacob cur_date {} !'.format(
                                    cur_date
                                ))
                                in_violation = True

                        # Check state of violation; if True, suspend
                        if in_violation is True:
                            _logger.info('Jacob suspending!')
                            subscription_id.action_suspend()
                        # If violation false and subscription is suspended
                        # Then activate it
                        elif subscription_id.stage_id.name == 'suspended':
                            _logger.info('Jacob activating!')
                            _logger.info('Jacob stage id is {}!'.format(subscription_id.stage_id.name))
                            subscription_id.action_re_activate()
                        # Default state print to confirm inspection for testng
                        else:
                            _logger.info('Jacob no action needed for customer')

                # Else there are no open invoices, verify services are active
                elif subscription_id.stage_id.name == 'suspended':
                    _logger.info('Jacob activating!')
                    _logger.info('Jacob stage id is {}!'.format(subscription_id.stage_id.name))
                    subscription_id.action_re_activate()
                # Default state print to confirm inspection for testng
                else:
                    _logger.info('Jacob no action needed for customer')
                    _logger.info('Jacob stage id is {}!'.format(subscription_id.stage_id.name))

            except RuntimeError as error:
                msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
                raise UserError(msg)
