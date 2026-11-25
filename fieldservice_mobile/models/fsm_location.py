# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class FSMLocation(models.Model):
    _inherit = "fsm.location"

    @api.model
    def get_mobile_contact_info(self, location_ids):
        """Return contact/owner many2ones for mobile, bypassing portal partner ACL.

        Portal workers can read ``fsm.location`` but often cannot ``name_get``
        the related ``res.partner`` rows, which left the Contact tile empty.
        """
        if not location_ids:
            return []
        locations = self.sudo().browse(location_ids).exists()
        result = []
        for loc in locations:
            contact = loc.contact_id
            owner = loc.owner_id
            result.append(
                {
                    "id": loc.id,
                    "contact_id": [contact.id, contact.display_name]
                    if contact
                    else False,
                    "owner_id": [owner.id, owner.display_name] if owner else False,
                }
            )
        return result

    @api.model
    def get_mobile_location_details(self, location_ids):
        """Return location detail fields for the mobile Location tile.

        Portal ACLs often fail ``search_read`` when related partners / territory
        cannot be name-resolved, which left the Location screen blank.
        """
        if not location_ids:
            return []
        locations = self.sudo().browse(location_ids).exists()
        result = []
        for loc in locations:
            contact = loc.contact_id
            owner = loc.owner_id
            territory = loc.territory_id
            result.append(
                {
                    "id": loc.id,
                    "name": loc.display_name or "",
                    "contact_address": loc.contact_address or "",
                    "owner_id": [owner.id, owner.display_name] if owner else False,
                    "contact_id": [contact.id, contact.display_name]
                    if contact
                    else False,
                    "phone": loc.phone or "",
                    "mobile": loc.mobile or "",
                    "ref": loc.ref or "",
                    "territory_id": [territory.id, territory.display_name]
                    if territory
                    else False,
                    "partner_latitude": loc.partner_latitude or 0.0,
                    "partner_longitude": loc.partner_longitude or 0.0,
                    "direction": loc.direction or "",
                }
            )
        return result
