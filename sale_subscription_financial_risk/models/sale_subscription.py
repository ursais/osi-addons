# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    # Calculates and returns a timedelta based on the customer's credit terms
    def _get_delta_qty(self, qty, uom):
        _logger.info("jacob called _get_delta_qty")
        if uom == 'days':
            delta_qty = timedelta(days=qty)
        elif uom == 'weeks':
            delta_qty = relativedelta(weeks=qty)
        elif uom == 'months':
            delta_qty = relativedelta(months=qty)
        elif uom == 'years':
            delta_qty = relativedelta(years=qty)
        _logger.info("Jacob delta_qty is {}".format(delta_qty))
        return delta_qty

    # May be called by an account.invoice onchange/payment received or
    # by the batch loop cron sale_subscription_financial_risk_suspend.xml
    @api.model
    def check_service_suspensions(self):
        _logger.info("Jacob called check_service_suspensions")
        for subscription in self:
            _logger.info("Jacob checking partner name {}".format(subscription.partner_id.name))
            try:
                # get list of open invoices, sorted by oldest open
                open_invoices = self.env['account.invoice'].search(
                    [('partner_id', '=', subscription.partner_id.id),
                     ('state', '=', 'open')],
                    order="date_due asc")
                cur_date = date.today()
                suspended_stage_id = self.env.ref(
                    'sale_subscription_suspend.'
                    'sale_subscription_stage_suspend').id

                # Calculate the delta_qty allowable for aging invoices
                delta_qty = subscription._get_delta_qty(
                    subscription.partner_id.overdue_limit_qty,
                    subscription.partner_id.overdue_limit_uom)
                if open_invoices:
                    _logger.info("Jacob found open invoices for parnter")
                    # Compute their credit and their credit limit based on type
                    # Using the oldest open invoice
                    # Inspected fixed credit based limits
                    if subscription.partner_id.credit_limit_type == 'fixed':
                        _logger.info("Jacob confirmed credit_limit_type == Fixed")
                        # format the credit float to prevent precision error
                        formatted_credit = format(
                            subscription.partner_id.credit, '.2f')

                        # Check for violation by credit limit
                        if float(formatted_credit) > subscription.\
                                partner_id.credit_limit:
                            _logger.info("Jacob suspending because credit limit amount is exceeded")
                            subscription.action_suspend()
                        # Check for violation by invoice age
                        elif open_invoices[0].date_due + delta_qty < cur_date:
                            _logger.info("Jacob suspending because invoice date is past allowable days")
                            subscription.action_suspend()
                        # Otherwise, re-activate everything if suspended
                        elif subscription.stage_id.id == \
                                suspended_stage_id:
                            _logger.info("Jacob re-activating service")
                            subscription.action_re_activate()
                        _logger.info("Jacob no action was taken")

                    # Inspecting subscription-based credit limits
                    elif subscription.partner_id.credit_limit_type == \
                            'subscription_based':
                        _logger.info("Jacob confirmed credit_limit_type == Subscription")

                        delta_mod = subscription._get_delta_qty(
                            subscription.partner_id.
                            credit_limit_subscription_qty,
                            subscription.partner_id.
                            credit_limit_subscription_uom)
                        # filter open_invoices list to valid sub range
                        valid_invoices = filter(
                            lambda invoice:
                            invoice.date_due + delta_mod > cur_date,
                            open_invoices)

                        # Bool to hold whether a partner is in violation or not
                        # do subscription_id.partner_id.risk_exception instead?
                        suspend = False

                        # Check for violation for invoices in valid range
                        for invoice in valid_invoices:
                            # if the invoice is in violation, suspend
                            if invoice.date_due + delta_qty < cur_date:
                                suspend = True

                        # Check state of violation; if True, suspend
                        if suspend:
                            _logger.info("Jacob suspending subscription service")
                            subscription.action_suspend()
                        # If violation false and subscription is suspended
                        # Then activate it
                        elif subscription.stage_id.id == suspended_stage_id:
                            _logger.info("Jacob re-activating subscription service")
                            subscription.action_re_activate()

                # Else there are no open invoices, verify services are active
                elif subscription.stage_id.id == suspended_stage_id:
                    _logger.info("Jacob no open invoices, re-activating service")
                    subscription.action_re_activate()

            except RuntimeError as error:
                msg = _('Error Encountered:\n {} \n {}'.format(
                    error, error.args))
                raise UserError(msg)
