# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class FSMPerson(models.Model):
    _inherit = "fsm.person"

    @api.model
    def update_mobile_gps(self, latitude, longitude, accuracy=0.0, loc_time=None):
        """Update GPS on the current user's own worker profile (portal-safe).

        Portal workers have write ACL on ``fsm.person`` but related tracking
        field writes can still fail under partner record rules; this method
        verifies ownership then writes with sudo.
        """
        person = self.search(
            [("partner_id", "=", self.env.user.partner_id.id)], limit=1
        )
        if not person:
            raise UserError(self.env._("No FSM worker is linked to this user."))
        if person.partner_id != self.env.user.partner_id:
            raise AccessError(self.env._("You can only update your own GPS location."))
        vals = {}
        # fieldservice_tracking fields — skip quietly if module is not installed
        if "track_lat" in person._fields:
            vals["track_lat"] = latitude
            vals["track_long"] = longitude
            vals["loc_rad"] = accuracy
            vals["loc_time"] = loc_time or fields.Datetime.now()
        if not vals:
            raise UserError(
                self.env._(
                    "Worker GPS tracking fields are not available. "
                    "Install fieldservice_tracking."
                )
            )
        person.sudo().write(vals)
        return True
