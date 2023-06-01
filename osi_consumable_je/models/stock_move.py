from ...stock_account.models.stock_move import StockMove as SM
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, svl_id, description):
        self.ensure_one()
        res = super()._generate_valuation_lines_data(partner_id=partner_id, qty=qty, debit_value=debit_value, credit_value=credit_value,
                                                     debit_account_id=debit_account_id, credit_account_id=credit_account_id,
                                                     svl_id=svl_id, description=description)
        if self.product_id.type == 'consu' and self.purchase_line_id:
            expense_account = self.product_id.product_tmpl_id._get_product_accounts().get('expense')
            input_account = self.product_id.product_tmpl_id._get_product_accounts().get('stock_input')
            debit_line_vals = {
                'name': description,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'balance': debit_value,
                'account_id': self.origin_returned_move_id and input_account.id or expense_account.id,
            }

            credit_line_vals = {
                'name': description,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'balance': -credit_value,
                'account_id': self.origin_returned_move_id and expense_account.id or input_account.id,
            }

            rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
            if credit_value != debit_value:
                # for supplier returns of product in average costing method, in anglo saxon mode
                diff_amount = debit_value - credit_value
                price_diff_account = self.env.context.get('price_diff_account')
                if not price_diff_account:
                    raise UserError(
                        _('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

                rslt['price_diff_line_vals'] = {
                    'name': self.name,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'balance': -diff_amount,
                    'ref': description,
                    'partner_id': partner_id,
                    'account_id': price_diff_account.id,
                }
            return rslt
        return res


def _account_entry_move(self, qty, description, svl_id, cost):
    """ Accounting Valuation Entries """
    self.ensure_one()
    am_vals = []
    if self.product_id.type != 'product':
        if self.product_id.type == 'consu' and self.purchase_line_id:
            pass
        else:
            return am_vals
    if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id:
        # if the move isn't owned by the company, we don't make any valuation
        return am_vals

    import pdb;pdb.set_trace()
    company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
    company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

    journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    # Create Journal Entry for products arriving in the company; in case of routes making the link between several
    # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
    if self._is_in():
        if self._is_returned(valued_type='in'):
            am_vals.append \
                (self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
        else:
            am_vals.append \
                (self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

    # Create Journal Entry for products leaving the company
    if self._is_out():
        cost = -1 * cost
        if self._is_returned(valued_type='out'):
            am_vals.append \
                (self.with_company(company_from).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
        else:
            am_vals.append \
                (self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))

    if self.company_id.anglo_saxon_accounting:
        # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
        if self._is_dropshipped():
            if cost > 0:
                am_vals.append \
                    (self.with_company(self.company_id)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
            else:
                cost = -1 * cost
                am_vals.append \
                    (self.with_company(self.company_id)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
        elif self._is_dropshipped_returned():
            if cost > 0:
                am_vals.append \
                    (self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals
                        (acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
            else:
                cost = -1 * cost
                am_vals.append \
                    (self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals
                        (acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))

    return am_vals


SM._account_entry_move = _account_entry_move
