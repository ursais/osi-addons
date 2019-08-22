from odoo import models, fields, api
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    # Calculates and returns a timedelta based on the customer's credit terms
    def _get_delta_qty(self, qty, uom):
        if uom == 'days':
            delta_qty = timedelta(days=qty)
        elif uom == 'weeks':
            delta_qty = relativedelta(weeks=qty)
        elif uom == 'months':
            delta_qty = relativedelta(months=qty)
        elif uom == 'years':
            delta_qty = relativedelta(years=qty)
        return delta_qty

    # May be called by an account.invoice onchange/payment received or
    # by the batch loop cron sale_subscription_financial_risk_suspend.xml
    @api.model
    def check_service_suspensions(self):
        for subscription_id in self:
            try:
                # get list of open invoices, sorted by oldest open
                open_invoices = subscription_id.env['account.invoice'].search(
                    [
                        ('partner_id', '=', subscription_id.partner_id.id),
                        ('state', '=', 'open')
                    ],
                    order="date_due asc"
                )
                if open_invoices:
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

                        # format the credit float to prevent precision error
                        formatted_credit = format(
                            subscription_id.partner_id.credit, '.2f'
                        )

                        # Check for violation by credit limit
                        if float(formatted_credit) > subscription_id.\
                                partner_id.credit_limit:
                            subscription_id.action_suspend()
                        # Check for violation by invoice age
                        elif open_invoices[0].date_due + delta_qty < cur_date:
                            subscription_id.action_suspend()
                        # Otherwise, re-activate everything if suspended
                        elif subscription_id.stage_id.name.lower() == \
                                'suspended':
                            subscription_id.action_re_activate()

                    # Inspecting subscription-based credit limits
                    elif subscription_id.partner_id.credit_limit_type == \
                            'subscription_based':
                        cur_date = date.today()

                        # Calculate the delta_qty allowable for aging invoices
                        delta_qty = subscription_id._get_delta_qty(
                            subscription_id.partner_id.overdue_limit_qty,
                            subscription_id.partner_id.overdue_limit_uom
                        )

                        # Determine delta modifier to define invoice range
                        if subscription_id.partner_id.\
                                credit_limit_subscription_uom != 'quarters':
                            delta_mod = subscription_id._get_delta_qty(
                                subscription_id.partner_id.
                                credit_limit_subscription_qty,
                                subscription_id.partner_id.
                                credit_limit_subscription_uom
                            )
                            # filter open_invoices list to valid sub range
                            valid_invoices = filter(
                                lambda invoice:
                                    invoice.date_due + delta_mod > cur_date,
                                    open_invoices
                            )
                        # if invoice range is quarters, identify active quarter
                        else:
                            # determine which quarter month belongs in
                            cur_quarter = cur_date.month // 3 + 1
                            # filter open_invoices list to active quarter
                            valid_invoices = filter(
                                lambda invoice:
                                    (invoice.date_due.month // 3 + 1) ==
                                    cur_quarter,
                                    open_invoices
                            )

                        # Bool to hold whether a partner is in violation or not
                        # do subscription_id.partner_id.risk_exception instead?
                        in_violation = False

                        # Check for violation for invoices in valid range
                        for invoice in valid_invoices:
                            # if the invoice is in violation, suspend
                            if invoice.date_due + delta_qty < cur_date:
                                in_violation = True

                        # Check state of violation; if True, suspend
                        if in_violation is True:
                            subscription_id.action_suspend()
                        # If violation false and subscription is suspended
                        # Then activate it
                        elif subscription_id.stage_id.name.lower() == \
                                'suspended':
                            subscription_id.action_re_activate()

                # Else there are no open invoices, verify services are active
                elif subscription_id.stage_id.name.lower() == 'suspended':
                    subscription_id.action_re_activate()

            except RuntimeError as error:
                msg = _(
                    'Error Encountered:\n {} \n {}'.format(
                        error, error.args
                    )
                )
                raise UserError(msg)
