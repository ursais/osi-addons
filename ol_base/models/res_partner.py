# Import Odoo libs
from odoo import _, api, fields, models


class ResPartner(models.Model):
    """Inherit res partner for field and methods."""

    _inherit = "res.partner"

    # COLUMNS #####

    override_company_name = fields.Text(string="Override Company")

    # END #########
    # METHODS #####

    def _fields_sync(self, vals):
        """
        If a child partner is a company, we don't want it's address fields to be
        updated if the parent company address changes.
        """
        # 1) let the core tell us which fields it treats as “address”
        address_fields = super()._address_fields()

        # 2) pop out any address changes so the built-in sync won’t propagate them to *all* children
        address_vals = {f: vals.pop(f) for f in address_fields if f in vals}

        # 3) run the rest of the normal sync (company_id, parent_id, etc.)
        super()._fields_sync(vals)

        # 4) now push address only to children that are not companies and contact
        if address_vals:
            for parent in self:
                to_update = parent.child_ids.filtered(
                    lambda c: not c.is_company and c.type == "contact"
                )
                if to_update:
                    to_update.write(address_vals)

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
