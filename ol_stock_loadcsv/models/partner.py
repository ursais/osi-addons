# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####
    csv_company_name = fields.Char("CSV Company Name")
    # END #########

    def name_get(self):
        """
        Overwrite the core name_get function for csv imported orders
        """

        # Only change name_get() functionality
        # if we show it on a Stock Picking's partner_shipping_id field
        if not self.env.context.get(
            "picking_partner_shipping_id", False
        ) or not self.env.context.get("picking_id", False):
            return super().name_get()

        picking = self.env["stock.picking"].browse(
            int(self.env.context.get("picking_id"))
        )

        # Only change name_get() functionality if the picking was created via CSV import
        if not picking.csv_import:
            return super().name_get()

        res = []
        for partner in self:
            if not partner.id == picking.csv_partner_shipping_id.id:
                # We don't want to override other partner's name_get functionality
                continue

            # Code below is taken from core: odoo13/odoo/addons/base/models/res_partner.py from _get_name()
            # ----- START -----
            name = partner.name or ""

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ["invoice", "delivery", "other"]:
                    name = dict(self.fields_get(["type"])["type"]["selection"])[
                        partner.type
                    ]
                # Use the company name originally defined in uploaded CSV
                if partner.csv_company_name:
                    name = f"{partner.csv_company_name}, {name}"
                # elif, continue with the core code
                elif not partner.is_company:
                    name = self._get_contact_name(partner, name)
            if self._context.get("show_address_only"):
                name = partner._display_address(without_company=True)
            if self._context.get("show_address"):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace("\n\n", "\n")
            name = name.replace("\n\n", "\n")
            if self._context.get("address_inline"):
                name = name.replace("\n", ", ")
            if self._context.get("show_email") and partner.email:
                name = f"{name} <{partner.email}>"
            if self._context.get("html_format"):
                name = name.replace("\n", "<br/>")
            if self._context.get("show_vat") and partner.vat:
                name = f"{name} - {partner.vat}"
            # Code above is taken from core: odoo13/odoo/addons/base/models/res_partner.py from _get_name()
            # ----- END -----
            res.append((partner.id, name))
        return res
