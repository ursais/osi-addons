from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_price_diff_account(self):
        # force the price difference account to be taken from the price
        # different properties as they were in the previous Odoo versions
        self.ensure_one()
        if self.product_id.cost_method != "standard":
            # product variable needed, pre-commit trolling with 88 character
            product = self.product_id
            debit_pdiff_account = (
                product.property_account_creditor_price_difference
                or product.categ_id.property_account_creditor_price_difference_categ
            )
            debit_pdiff_account = self.move_id.fiscal_position_id.map_account(
                debit_pdiff_account
            )
            return debit_pdiff_account
        return super()._get_price_diff_account()
