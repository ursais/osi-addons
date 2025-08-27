# Import Odoo libs
from odoo import _, api, fields, models


class ResPartner(models.Model):
    """Inherit res partner for field and methods."""

    _inherit = "res.partner"

    # COLUMNS #####

    override_company_name = fields.Text(string="Override Company")

    # END #########
    # METHODS #####

    @api.depends(
        "complete_name",
        "email",
        "vat",
        "state_id",
        "country_id",
        "commercial_company_name",
    )
    @api.depends_context(
        "show_address",
        "partner_show_db_id",
        "address_inline",
        "show_email",
        "show_vat",
        "lang",
    )
    def _compute_display_name(self):
        super()._compute_display_name()
        for partner in self:
            if self.env.context.get("partner_address_details", False):
                name = partner.name or ""
                contact_type = partner.type
                address = ""
                if not self.env.context.get("hide_address", False) and (
                    partner.street or partner.city
                ):
                    street = partner.street or ""
                    city = partner.city or ""
                    if not partner.is_company and partner.commercial_company_name:
                        address = f"({street} {city})"
                    else:
                        address = f"({street} {city})"

                company = ""
                if partner.company_name or partner.parent_id and not partner.is_company:
                    company = (
                        f"{partner.commercial_company_name or partner.parent_id.name},"
                    )

                if partner.is_company:
                    name = f"{name} {address}"
                else:
                    name = f"{company} {name} {address}"

                partner.display_name = name.strip()

    # END #########
