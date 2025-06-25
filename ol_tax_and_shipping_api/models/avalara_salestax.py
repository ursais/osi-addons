import logging
import uuid as uuid_lib

from odoo import models


class AvalaraSalestax(models.Model):
    _inherit = "avalara.salestax"

    def create_transaction(
        self,
        doc_date,
        doc_code,
        doc_type,
        partner,
        ship_from_address,
        shipping_address,
        lines,
        user=None,
        exemption_number=None,
        exemption_code_name=None,
        commit=False,
        invoice_date=None,
        reference_code=None,
        location_code=None,
        is_override=None,
        currency_id=None,
        ignore_error=None,
        log_to_record=False,
    ):

        result = super().create_transaction(
            doc_date=doc_date,
            doc_code=doc_code,
            doc_type=doc_type,
            partner=partner,
            ship_from_address=ship_from_address,
            shipping_address=shipping_address,
            lines=lines,
            user=user,
            exemption_number=exemption_number,
            exemption_code_name=exemption_code_name,
            commit=commit,
            invoice_date=invoice_date,
            reference_code=reference_code,
            location_code=location_code,
            is_override=is_override,
            currency_id=currency_id,
            ignore_error=ignore_error,
            log_to_record=log_to_record,
        )

        if self.env.context.get("is_tax_and_shipping_call"):
            # Get the Integer representation of the UUID
            # so the core OCA code can correctly convert the value to an Int
            for line in result["lines"]:
                line["lineNumber"] = uuid_lib.UUID(line["lineNumber"]).int
        return result
