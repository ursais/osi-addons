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
