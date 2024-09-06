# Import Odoo Libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        compute="_compute_check_hot_ar",
        store=True,
        help="""Customer has one or more invoices that are
         overdue and past the grace period.""",
    )
    override_hot_ar = fields.Boolean(
        string="Override Hot AR",
        help="""ustomer has one or more invoices that are overdue and
         past the grace period.""",
        groups="account.group_account_invoice",
    )

    # END #########

    # METHODS #####

    @api.depends("invoice_ids.hot_ar")
    def _compute_check_hot_ar(self):
        """Update hot_ar bool if any invoices have it enabled."""
        for partner in self:
            if partner.override_hot_ar:
                partner.hot_ar = False
            else:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("payment_state", "not in", ("in_payment", "paid", "reversed")),
                        ("move_type", "in", ("out_invoice", "in_invoice", "out_refund", "in_refund")),
                        ("hot_ar", "=", True),
                        ("override_hot_ar", "=", False),
                    ]
                )
                partner.hot_ar = bool(invoices)

    # END #########
