# Import Odoo libs
from odoo import api, fields, models
from odoo.tools.misc import formatLang
from odoo.addons.ol_pdf_reports.models.tools import newline_to_br


class PurchaseOrder(models.Model):
    """
    Adding fields, defaults and report data methods to Purchase Order.
    """

    _inherit = "purchase.order"

    # COLUMNS ##########

    approved_vendor = fields.Boolean(
        related="partner_id.approved_vendor",
        help="Indicates if the vendor is approved for purchasing.",
    )
    shipping_notes = fields.Text(
        string="Shipping Notes",
    )
    contact_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Contact",
    )
    delivery_method_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Delivery Method",
    )

    # END ##########
    # METHODS ######

    @api.model
    def get_supplier_defaults(self, partner_id):
        """
        Get a partner's shipping preferences so we can update PO fields.
        """
        if not partner_id:
            return {}

        # Get default contacts
        default_contacts = partner_id.default_supplier_contact_ids

        return {
            "contact_ids": (
                [contact.id for contact in default_contacts] if default_contacts else []
            ),
            "shipping_notes": partner_id.default_shipping_notes or False,
            "delivery_method_id": (
                partner_id.supplier_delivery_method_id.id
                if partner_id.supplier_delivery_method_id
                else False
            ),
            "incoterm_id": (
                partner_id.default_incoterms_id.id
                if partner_id.default_incoterms_id.id
                else False
            ),
        }

    @api.onchange(
        "partner_id",
        "company_id",
    )
    def onchange_partner_id(self):
        """
        Get the new partner's default shipping preferences when changed.
        """
        res = super().onchange_partner_id()
        self.update(self.get_supplier_defaults(self.partner_id))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        When creating a new PO, set the supplier defaults if the supplier is set
        """
        for val in vals_list:
            if val.get("partner_id"):
                partner = self.env["res.partner"].browse(val["partner_id"])
                for key, value in self.get_supplier_defaults(partner).items():
                    if not val.get(key):
                        val[key] = value

            return super().create(val)

    def get_purchase_order_doc_data(self):
        """
        Get data for the purchase order doc report
        """
        self.ensure_one()
        billing_partner = self.company_id.partner_id
        ap_contacts = billing_partner
        res = {
            "shipping_notes": (
                newline_to_br(self.shipping_notes) if self.shipping_notes else ""
            ),
            "supplier_notes": newline_to_br(self.notes) if self.notes else "",
            "amount_untaxed": formatLang(
                self.env, self.amount_untaxed, currency_obj=self.currency_id
            ),
            "amount_tax": formatLang(
                self.env, self.amount_tax, currency_obj=self.currency_id
            ),
            "amount_total": formatLang(
                self.env, self.amount_total, currency_obj=self.currency_id
            ),
            "billing_name": billing_partner.commercial_company_name
            or billing_partner.name
            or "",
            "billing_email": ap_contacts[0].email if ap_contacts else "",
            "billing_address": newline_to_br(billing_partner.contact_address),
            "shipping_address": newline_to_br(
                self.dest_address_id.contact_address
                if self.dest_address_id
                else billing_partner.contact_address
            ),
        }
        terms = self.payment_term_id
        if not terms:
            terms = self.partner_id.property_supplier_payment_term_id
        res["payment_terms"] = terms.name if terms else ""

        if self.state in ("draft", "sent"):
            # If this is being sent as part of a RFQ email, this context is set to True
            if self.env.context.get("send_rfq", False):
                # the order is not in a confirmed state,
                # but we're creating the doc as if it were
                res["order_date"] = fields.Date.context_today(self)
                res["submitted_by"] = self.env.user.name

        res["lines"] = []
        for line in self.order_line.filtered(lambda x: x.product_id):
            cur_tariff_code = line.product_id.tariff_code_id
            tariff_code_line = ""
            if cur_tariff_code.code:
                tariff_code_line = (
                    f"{cur_tariff_code.type_id.label}: {cur_tariff_code.code}"
                )

            res["lines"].append(
                {
                    "name": line.product_id.name,
                    "sku": line.product_id.get_supplier_code(supplier=self.partner_id),
                    "qty": line.product_qty,
                    "unit_price": formatLang(
                        self.env, line.price_unit, currency_obj=self.currency_id
                    ),
                    "line_subtotal": formatLang(
                        self.env, line.price_subtotal, currency_obj=self.currency_id
                    ),
                    "line_note": newline_to_br(line.note) if line.note else "",
                    "product_tariff_code": tariff_code_line,
                }
            )

        return res

    # END ##########
