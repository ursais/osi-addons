# Import Odoo libs
from odoo import fields, models

# Import Python libs
import re


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####
    csv_company_name = fields.Char("CSV Company Name")
    # END #########

    def _compute_display_name(self):
        result = super()._compute_display_name()

        # TODO: Need to check, this method is needed or not.
        context = dict(self.env.context)
        # Only change display_name functionality
        # if we show it on a Stock Picking's partner_shipping_id field
        if not context.get("picking_partner_shipping_id", False) or context.get(
            "picking_id", False
        ):
            return result
        picking = self.env["stock.picking"].browse(int(context.get("picking_id")))
        # Only change display_name functionality if the picking was created via CSV import
        if not picking.csv_import:
            return result

        for partner in self:
            if not partner.id == picking.csv_partner_shipping_id.id:
                # We don't want to override other partner's display_name functionality
                continue

            # ----- START -----
            name = partner.with_context({"lang": self.env.lang})._get_complete_name()
            # Use the company name originally defined in uploaded CSV
            if partner.csv_company_name:
                name = f"{partner.csv_company_name}, {name}"
            if partner._context.get("show_address"):
                name = name + "\n" + partner._display_address(without_company=True)
            name = re.sub(r"\s+\n", "\n", name)
            if partner._context.get("partner_show_db_id"):
                name = f"{name} ({partner.id})"
            if partner._context.get("address_inline"):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get("show_email") and partner.email:
                name = f"{name} <{partner.email}>"
            if partner._context.get("show_vat") and partner.vat:
                name = f"{name} ‒ {partner.vat}"
            # ----- END -----

            partner.display_name = name.strip()
        return result
