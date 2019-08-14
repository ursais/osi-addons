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

    # partner_credit_type = fields.Selection()
    # partner_credit_limit = fields.Float()
    # partner_credit = fields.Monetary()
    # service = fields.Many2one()

    # These functions are in agreement_sale_subscription_suspension Ken did
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

    # CRON will loop through all records in the model
    @api.model
    def check_service_suspensions(self, single_partner=None):
        # accepts opitonal passed partner_id to match subscriptions on
        try:
            # grab the timezone, format into a datetime
            # then add QTY based on UOM
            # Then compare to oldest_invoice due_date and see if
            # it is in violation
            # user_tz = timezone(self.env.context.get('tz') or
            #                     self.env.use.tz or 'UTC')
            # curDate = datetime.now().strftime('%m/%d/%Y')

            curDate = date.today()

            deltaQty = timedelta(days=self.partner_id.overdue_limit_qty)
            if self.partner_id.overdue_limit_uom == 'days':
                deltaQty = timedelta(days=self.partner_id.overdue_limit_qty)
            elif self.partner_id.overdue_limit_uom == 'weeks':
                deltaQty = timedelta(weeks=self.partner_id.overdue_limit_qty)
            elif self.partner_id.overdue_limit_uom == 'months':
                deltaQty = timedelta(months=self.partner_id.overdue_limit_qty)

            # time_now = datetime.now()
            _logger.info('Jacob time_now is {}'.format(
                curDate)
            )
            # due_date is as "08/12/2019"
            # if a specific partner record is passed, do an individual match
            # if single_partner:
            #     _logger.info('Jacob passed a partner {}'.format(
            #         single_partner)
            #     )
            #     self.partner_subscriptions = self.env['sale.subscription'].search(
            #         [
            #             ('partner_id', '=', single_partner)
            #         ]
            #     )
            #     for sub in self.partner_subscriptions:
            #         _logger.info('Jacob in for service-in-subscription loop')
            #         # need to call Brian's function as a super
            #         self.action_re_activate()
            # # else default to processing/auditing all partner records
        # else:
        # Skipping the passed partner for now
            _logger.info('Jacob starting suspension check batch')
            # get the age of the oldest open invoice
            # whenever trying to get a field, use seach([])
            oldest_invoice = self.env['account.invoice'].search(
                [
                    ('partner_id', '=', self.partner_id),
                    ('state', '=', 'open')
                ],
                order="due_date asc"
            )
            _logger.info('Jacob grabbed oldest invoice')

            # compute their credit and their credit limit
            # (based on the type)
            if self.partner_id.credit_limit_type == 'fixed':
                _logger.info('Jacob partner credit type {}'.format(
                    self.partner_id.credit_limit_type)
                )
                if self.partner_id.credit > self.partner_id.credit_limit:
                    _logger.info('Jacob suspending!')
                    self.action_suspend()
                elif oldest_invoice[0].due_date + deltaQty > curDate:
                    _logger.info('Jacob suspending!')
                    self.action_suspend()
                else:
                    _logger.info('Jacob activating!')
                    self.action_re_activate()
            # Same thing, but for subscription-based credit limits
            elif self.partner_id.credit_limit_type == 'subscription_based':
                _logger.info('Jacob partner credit type {}'.format(
                    self.partner_id.credit_limit_type)
                )
                # grab the timezone, format into a datetime, add QTY based
                # on UOM
                # THen compare to oldest_invoice due_date and see if it is
                # in violation
                # self.partner_id.credit_limit_subscription_qty
                # self.partner_id.credit_limit_subscription_uom

                # if self.partner_id.credit > self.partner_id.credit_limit:
                #     self.action_suspend()
                # elif oldest_invoice[0].due_date  self.:
                #     self.action_suspend()
                # else:
                #     self.action_re_activate()

        except RuntimeError as error:
            msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
            raise UserError(msg)
