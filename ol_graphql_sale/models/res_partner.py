# Import Python Libs
import re

# Import Odoo libs
from odoo import models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "res.partner"
    _inherit = ["res.partner", "graphql.mixin"]

    def get_partner_by_email(self, email, tid):
        """
        Try to find the partner with an broader and broader domain
        We do this to ensure we find the "best possible" partner based on the email address
        """
        domain = [("email", "=ilike", email), ("type", "=", "contact")]
        res = False
        indexes = list(range(len(domain)))
        indexes.reverse()
        for idx in indexes:
            # we want to prioritize certain records over others, so fetch all active records
            res = self.env["res.partner"].search(domain, order="id asc")
            # filter out the company records as a fallback if no non-company customers are found
            company_partners = res.filtered(lambda partner: (partner.is_company))
            # the remaining records in res represent the contact type partners
            contact_partners = res - company_partners
            # prioritize the contact type first
            related_recs = contact_partners or company_partners
            # if records exist, but none have matched our criteria, log it
            if not related_recs and res:
                self.log_warning_message(
                    f"Attempting partner matching using email {email} "
                    f"| No well-formed contact or company-type partner found, but these records exist: {res}",
                    tid=tid,
                )
            if related_recs:
                return related_recs[0]

            domain = domain[:idx]

        return self.find_related_odoo_record(
            odoo_object=self.env["res.partner"],
            field_name="email",
            value=email,
            tid=tid,
        )

    @api.constrains("vat")
    def check_vat(self):
        """
        Suppress failures when running through GraphQL
        Updates function in base_vat/models/res_partner.py
        """
        if self.env.context.get("graphql_incoming_message"):
            try:
                return super(ResPartner, self).check_vat()
            except ValidationError as e:
                # Allow the partner to continue with incorrect VAT
                self.log_exception_message(
                    "Error validating VAT number while processing GraphQL message"
                )
                self.message_post(body="Error validating VAT number: {}".format(e))
        else:
            return super(ResPartner, self).check_vat()
