# Import Odoo libs
from odoo import fields, models
from odoo.tools.misc import formatLang
from odoo.addons.ls_pdf_reports.models.tools import newline_to_br


class PurchaseOrder(models.Model):
    """
    Adding fields to Purchase Order.
    """

    _inherit = "purchase.order"

    # COLUMNS ##########

    approved_vendor = fields.Boolean(
        related="partner_id.approved_vendor",
        help="Indicates if the vendor is approved for purchasing.",
    )

    # END ##########

    """Get reporting information from a purchase order"""
    def get_purchase_order_doc_data(self):
        """
        Get data for the purchase order doc report
        """
        self.ensure_one()
        billing_partner = self.company_id.partner_id
        # TODO: "billing_partner.get_contacts()" method not found
        # ap_contacts = billing_partner.get_contacts('ap').filtered('email')
        ap_contacts = billing_partner
        res = {
            # TODO: "self.shipping_notes" field not found
            # 'shipping_notes': newline_to_br(self.shipping_notes) if self.shipping_notes else '',
            'shipping_notes': '',
            'supplier_notes': newline_to_br(self.notes) if self.notes else '',
            'amount_untaxed': formatLang(self.env, self.amount_untaxed, currency_obj=self.currency_id),
            'amount_tax': formatLang(self.env, self.amount_tax, currency_obj=self.currency_id),
            'amount_total': formatLang(self.env, self.amount_total, currency_obj=self.currency_id),
            'billing_name': billing_partner.commercial_company_name or billing_partner.name or '',
            'billing_email': ap_contacts[0].email if ap_contacts else '',
            'billing_address': newline_to_br(billing_partner.contact_address),
            'shipping_address': newline_to_br(
                self.dest_address_id.contact_address
                if self.dest_address_id
                else billing_partner.contact_address
            ),
        }
        terms = self.payment_term_id
        if not terms:
            terms = self.partner_id.property_supplier_payment_term_id
        res['payment_terms'] = terms.name if terms else ''

        if self.state in ('draft', 'sent'):
            # If this is being sent as part of a RFQ email, this context is set to True
            if self.env.context.get('send_rfq', False):
                # the order is not in a confirmed state, but we're creating the doc as if it were
                res['order_date'] = fields.Date.context_today(self)
                res['submitted_by'] = self.env.user.name

        res['lines'] = []
        for line in self.order_line:
            cur_tariff_code = line.product_id.tariff_code_id
            tariff_code_line = ''
            if cur_tariff_code.code:
                tariff_code_line = f'{cur_tariff_code.type_id.label}: {cur_tariff_code.code}'

            res['lines'].append(
                {
                    'name': line.product_id.name,
                    'sku': line.product_id.get_supplier_code(supplier=self.partner_id),
                    'qty': line.product_qty,
                    'unit_price': formatLang(self.env, line.price_unit, currency_obj=self.currency_id),
                    'line_subtotal': formatLang(self.env, line.price_subtotal, currency_obj=self.currency_id),
                    # TODO: "line.note" field not found
                    # 'line_note': newline_to_br(line.note) if line.note else '',
                    'line_note': newline_to_br(line.name) if line.display_type == 'line_note' else "",
                    'product_tariff_code': tariff_code_line,
                }
            )

        return res
