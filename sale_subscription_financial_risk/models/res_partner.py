# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Duration of overdue limit
    overdue_limit_qty = fields.Integer(
        string='Overdue Limit',
        help='If one invoice is due for more than the duration \
        specified here, all the subscriptions of the customer will \
        be suspended.',
        default=15)

    # Overdue limit unit of measurement
    overdue_limit_uom = fields.Selection(
        string='Unit of Measure',
        selection=[('days', 'Days'),
                   ('weeks', 'Weeks'),
                   ('months', 'Months')],
        default='days', required=True)

    # Hide the credit_limit field if "Credit Limit Type" is not "Fixed"
    credit_limit_type = fields.Selection(
        string='Credit Limit Type',
        selection=[('fixed', 'Fixed Amount'),
                   ('subscription_based', 'Based on Subscriptions')])

    # Hide these last 2 fields only if the type is not "Based on Subscriptions"
    credit_limit_subscription_qty = fields.Integer(
        string='Using the last', default=4)

    # Credit limit unit of measurement
    credit_limit_subscription_uom = fields.Selection(
        string='Unit of Measure',
        selection=[('weeks', 'Weeks'),
                   ('months', 'Months'),
                   ('quarters', 'Quarters'),
                   ('years', 'Years')],
        default='weeks', required=True)
