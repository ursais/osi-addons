# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # COLUMNS #####

    payment_preference = fields.Many2one(
        'res.paypref',
        string='Payment Preference',
        company_dependent=True
    )

    # END #########
