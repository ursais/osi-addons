# Import Odoo Libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    # COLUMNS #####

    hot_ar_grace_period = fields.Integer(
        string="Hot AR Grace Period",
        default=15,
        help="""Places holds on customer orders when invoices are not paid
         within grace period of being due."""
    )

    # END #########

    # METHODS #####

    @api.constrains('hot_ar_grace_period')
    def validate_hot_ar_grace_period(self):
        for record in self:
            if record.hot_ar_grace_period <= 0:
                raise ValidationError(_("Please set a strictly positive Hot AR Grace Period value."))

    # END #########
