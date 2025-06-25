import uuid as uuid_lib
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order"

    def _avatax_compute_tax(self):
        # No need for overrides if this is not a Tax and Shipping call
        if not self.env.context.get("is_tax_and_shipping_call"):
            return super()._avatax_compute_tax()

        """
        Full override of the OCA module's method for Tax & Shipping
        """

        """Contact REST API and recompute taxes for a Sale Order"""
        # Override to handle lines with split taxes (e.g. TN)
        self and self.ensure_one()
        doc_type = self._get_avatax_doc_type()
        Tax = self.env["account.tax"]
        avatax_config = self.company_id.get_avatax_config_company()
        if not avatax_config:
            return False
        partner = self.partner_id
        if avatax_config.use_partner_invoice_id:
            partner = self.partner_invoice_id
        taxable_lines = self._avatax_prepare_lines(self.order_line)
        tax_result = avatax_config.create_transaction(
            doc_date=self.date_order,
            doc_code=self.name,
            doc_type=doc_type,
            partner=partner,
            ship_from_address=self.warehouse_id.partner_id or self.company_id.partner_id,
            shipping_address=self.tax_address_id or self.partner_id,
            lines=taxable_lines,
            user=self.user_id,
            exemption_number=self.exemption_code or None,
            exemption_code_name=self.exemption_code_id.code or None,
            currency_id=self.currency_id,
            log_to_record=self,
        )
        tax_result_lines = {int(x["lineNumber"]): x for x in tax_result["lines"]}
        for line in self.order_line:
            # Get the Integer representation of the UUID, same as in `create_transaction`
            line_lookup_int = uuid_lib.UUID(line.uuid).int
            # Use this to find the correct line
            tax_result_line = tax_result_lines.get(line_lookup_int)
            # The Core line.
            # tax_result_line = tax_result_lines.get(line.id)
            if tax_result_line:
                # Should we check the rate with the tax amount?
                # tax_amount = tax_result_line["taxCalculated"]
                # rate = round(tax_amount / line.price_subtotal * 100, 2)
                # rate = tax_result_line["rate"]
                tax_calculation = 0.0
                if tax_result_line["taxableAmount"]:
                    tax_calculation = tax_result_line["taxCalculated"] / tax_result_line["taxableAmount"]
                rate = round(tax_calculation * 100, 4)
                tax = Tax.get_avalara_tax(rate, doc_type)
                if tax not in line.tax_id:
                    line_taxes = (
                        tax
                        if avatax_config.override_line_taxes
                        else tax | line.tax_id.filtered(lambda x: not x.is_avatax)
                    )
                    line.tax_id = line_taxes
                line.tax_amt = tax_result_line["tax"]
        self.tax_amount = tax_result.get("totalTax")
        return True


class TemporarySaleOrderLine:
    def __init__(self, OdooNewId):
        self._id = str(OdooNewId.uuid)

    @property
    def id(self):
        return self._id

    def __str__(self):
        return f"TemporarySaleOrderLine: {self._id}"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _avatax_prepare_line(self, sign=1, doc_type=None):
        """
        Handle Pseudo-ids for Sale Order Lines
        """
        res = super(SaleOrderLine, self)._avatax_prepare_line(sign=sign, doc_type=doc_type)
        if self.env.context.get("is_tax_and_shipping_call"):
            temp_id = TemporarySaleOrderLine(self)
            res.update({"id": temp_id, "line_number": temp_id.id})
        else:
            res.update({"line_number": self.id})
        return res
