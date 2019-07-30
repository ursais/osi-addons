from odoo import models, fields, api


class sale_subscription_financial_risk_partner(models.Model):
    _inherit = 'res.partner'

    # Duration of overdue limit
    overdue_limit_qty = fields.Integer(
        string='Overdue Limit',
        help='If one invoice is due for more than the duration \
        specified here, all the subscriptionsof the customer will \
        be suspended.'
    )

    # Overdue limit unit of measurement
    overdue_limit_uom = fields.Selection(
        string='Unit of Measure',
        selection=[
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months')
        ]
    )

    # Hide the credit_limit field if "Credit Limit Type" is not "Fixed"
    credit_limit_type = fields.Selection(
        string='Credit Limit Type',
        selection=[
            ('fixed', 'Fixed Amount'),
            ('subscription_based', 'Based on Subscription')
        ]
    )

    # Hide these last 2 fields only if the type is not "Based on Subscriptions"
    credit_limit_subscription_qty = fields.Integer(string='Using the last')

    # Credit limit unit of measurement
    credit_limit_subscription_uom = fields.Selection(
        string='Unit of Measure',
        selection=[
            ('weeks', 'Weeks'),
            ('months', 'Months'),
            ('quarters', 'Quarters'),
            ('years', 'Years')
        ]
    )
