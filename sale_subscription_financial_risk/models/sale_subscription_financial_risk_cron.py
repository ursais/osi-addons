# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _


class checkServiceSuspensionState(models.Model):
    _inherit = 'ir.cron'

    @api.multi
    def _check_service_suspensions(self, partner=None):
        try:
            # do individual match if a specific partner record is passed
            if partner:
                # do this like a many2one or use the domain in a search()?
                # domain = [('id', '=', 'partner')]
                # partner = res.partner.search(domain)
                partner_subscriptions = fields.Many2one(
                    'sale.subscription',
                    domain=[
                        ('partner_id', '=', partner)
                    ]
                )
                for service in partner_subscriptions:
                    # brian's extension should allow me to do this
                    service.action_re_activate()
                    # service.write({'stage_id': 'In Progress'})
            # default to processing all partner records
            else:
                # gather all valid, active subscriptions
                subscriptions = fields.Many2one(
                    'sale.subscription',
                    domain=[
                        '|',
                        ('stage_id', '=', 'In Progress'),
                        ('stage_id', '=', 'Suspended')
                    ]
                )
                for service in subscriptions:
                    # do this like a many2one or use the domain in a search()?
                    # get the partner record for each of the services
                    # domain = [('id', '=', 'service.partner_id')]
                    # partner = res.partner.search(domain)
                    # ...or...
                    partner = fields.Many2one(
                        'res.partner',
                        domain=[
                            ('id', '=', service.partner_id)
                        ]
                    )

                    # compute their credit and credit limit by credit type
                    # Can I just directly pull partner.credit_limit_type
                    # instead of using a related?
                    partner_credit_type = fields.Selection(
                        related='partner.credit_limit_type'
                    )
                    partner_credit_limit = fields.Float(
                        related='partner.credit_limit'
                    )
                    partner_credit = fields.Monetary(
                        related='partner.credit'
                    )

                    # compute their credit and credit limit by credit type
                    # ^^ how to compute their credit?  Var exists but not visbl
                    # compare the credit with their limit
                    if partner_credit_type == 'fixed':
                        # get the age of the oldest open invoice - how to view list

                        # if credit > credit limit or age > overdue limit then
                        # move all the subscriptions of the customer to "Suspended"
                        if partner_credit > partner_credit_limit:
                            service.action_suspend()
                            # service.write({'stage_id': 'Suspended'})
                    elif partner_credit_type == 'subscription_based':
                        # get the age of the oldest open invoice - how to view list
                        partner_credit_limit_subscription_qty = fields.Int(
                            related='partner.credit_limit_subscription_qty'
                        )
                        partner_credit_limit_subscription_uom = fields.Selection(
                            related='partner.credit_limit_subscription_uom'
                        )
                        # if credit > credit limit or age > overdue limit then
                        # move all the subscriptions of the customer to "Suspended"
                        if ...:
                            service.action_suspend()
                            # service.write({'stage_id': 'Suspended'})

                    # will need to be able to control exceptions
                    # res.partner needs a field that prevents suspension
                    # for eligible services (e.g. NWWSD, Luckey Farmers, etc)
                    # suspend/reactivate service as the case demands
                    # service.action_re_activate()
                    # service.write({'stage_id': 'In Progress'})
        except RuntimeError as error:
            msg = _('Error Encountered:\n {} \n {}'.format(error, error.args))
            raise UserError(msg)
