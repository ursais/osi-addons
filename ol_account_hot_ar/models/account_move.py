# Import Odoo Libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
    )
    override_hot_ar = fields.Boolean(
        string="Override Hot AR",
        help="Set this to true to ignore this invoice when creating Hot AR order holds.",
        groups="account.group_account_manager",
    )

    # END #########

    # METHODS #####

    @api.onchange('payment_state')
    def onchnage_payment_state(self):
        for invoice in self:
            if invoice.payment_state in ["in_payment", "paid", "reversed"]:
                invoice.hot_ar = False

    # END #########
