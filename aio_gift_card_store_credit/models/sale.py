# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        # call super method
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                if line.company_id.store_credit_product_id == line.product_id:
                    line.write({
                        'remaining_sc_amount': -(line.price_subtotal),
                        'sc_flag': True})
                if line.company_id.gift_card_product_id == line.product_id:
                    line.write({
                        'remaining_gift_amount': -(line.price_subtotal),
                        'gift_flag': True})
        return res

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False,
                        invoices are grouped by (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            group_key = order.id if grouped else \
                (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(
                    key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice,
                                 precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in \
                            invoices[group_key].origin.split(', '):
                        vals['origin'] = '{0}, {1}'.format(
                            invoices[group_key].origin,
                            order.name)
                    if order.client_order_ref and \
                            order.client_order_ref not in \
                            invoices[group_key].name.split(', '):
                        vals['name'] = '{0}, {1}'.format(
                            invoices[group_key].name,
                            order.client_order_ref)
                    invoices[group_key].write(vals)
                if line.qty_to_invoice > 0:
                    line.invoice_line_create(
                        invoices[group_key].id,
                        line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(
                        invoices[group_key].id,
                        line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            # Check whether this is Store credit or Gift Card case
            if invoice.sale_id:
                # set total for Store credit product
                sale_line_sc_id = self.env['sale.order.line'].search([
                    ('order_id', '=', invoice.sale_id.id),
                    ('sc_flag', '=', True)])
                # set total for Gift card product
                sale_line_gift_id = self.env['sale.order.line'].search([
                    ('order_id', '=', invoice.sale_id.id),
                    ('gift_flag', '=', True)])
            if not sale_line_sc_id and not sale_line_gift_id:
                if invoice.amount_untaxed < 0:
                    invoice.type = 'out_refund'
                    for line in invoice.invoice_line_ids:
                        line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes.
            # In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view(
                'mail.message_origin_link',
                values={'self': invoice,
                        'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    remaining_sc_amount = fields.Float(
        string='Remaining SC'
    )
    remaining_gift_amount = fields.Float(
        string='Remaining Gift Card'
    )
    sc_flag = fields.Boolean(
        string='Flag for SC amount',
        default=False
    )
    gift_flag = fields.Boolean(
        string='Flag for Gift Card amount',
        default=False
    )
    qty_to_invoice = fields.Float(
        compute='_compute_to_invoice_qty',
        string='To Invoice',
        store=True,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure')
    )
    qty_invoiced = fields.Float(
        compute='_compute_get_invoiced_qty',
        string='Invoiced',
        store=True,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty',
                 'order_id.state', 'remaining_sc_amount',
                 'remaining_gift_amount')
    def _compute_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice =\
                        line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice =\
                        line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
            # Check for Store Credit Line and its remaining amount
            if line.sc_flag:
                if line.remaining_sc_amount > 0:
                    line.qty_to_invoice = 1
                else:
                    line.qty_to_invoice = 0

            # Check for Gift Card Line and its remaining amount
            if line.gift_flag:
                if line.remaining_gift_amount > 0:
                    line.qty_to_invoice = 1
                else:
                    line.qty_to_invoice = 0

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _compute_get_invoiced_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity
        invoiced is decreased. Note that this is the case only if the refund
        is generated from the SO and that is intentional: if a refund made
        would automatically decrease the invoiced quantity, then there is a
        risk of reinvoicing it automatically, which may not be wanted at all.
        That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom)
                    elif invoice_line.invoice_id.type == 'out_refund':
                        qty_invoiced -= invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced
            # Check for Store Credit Line
            if (line.sc_flag or line.gift_flag) and (
                line.remaining_gift_amount > 0 or line.remaining_sc_amount > 0
            ):
                line.qty_invoiced = 0

    @api.multi
    def _prepare_invoice_line(self, qty):
        # call super method
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty=qty)
        # update sale line id
        if res:
            res.update({'sale_line_id': self.id})
        return res
