# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    authorize_fee_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Fee Product",
        help="Product used to record Authorize.net processing fees. "
        "The expense account configured on this product determines "
        "where fees are posted in the general ledger. When a payment "
        "is confirmed and fee rates are configured, a write-off line "
        "is added to the payment journal entry automatically.",
        domain="[('type', '=', 'service')]",
    )
    authorize_fee_pct = fields.Float(
        string="Fee (%)",
        digits=(5, 4),
        default=0.0,
        help="Authorize.net processing fee as a percentage of the "
        "transaction amount (e.g. 2.9 for 2.9%).",
    )
    authorize_fee_fixed = fields.Monetary(
        string="Fixed Fee",
        currency_field="main_currency_id",
        default=0.0,
        help="Authorize.net fixed per-transaction processing fee "
        "(e.g. 0.30 for $0.30).",
    )

    @api.onchange("authorize_fee_product_id")
    def _onchange_authorize_fee_product_id(self):
        """Warn if the selected fee product lacks an expense account."""
        if not self.authorize_fee_product_id:
            return
        product = self.authorize_fee_product_id
        accounts = product.product_tmpl_id.get_product_accounts()
        if not accounts.get("expense"):
            return {
                "warning": {
                    "title": _("Missing Expense Account"),
                    "message": _(
                        "The selected product '%(product)s' does not have "
                        "an expense account configured. Please set one on "
                        "the product or its category so that processing "
                        "fees are recorded correctly.",
                        product=product.display_name,
                    ),
                }
            }
