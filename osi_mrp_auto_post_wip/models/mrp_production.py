# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    def _cron_process_action_post_inventory_wip(self):
        mrp_ids = self.env["mrp.production"].search(
            [("state", "in", ["progress", "to_close"])]
        )
        for mrp_id in mrp_ids:
            try:
                mrp_id.action_post_inventory_wip()
            except Exception as e:
                # Get the todo activity type
                activity_type = self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1)
                
                # Create activity with error details
                mrp_id.activity_schedule(
                    activity_type_id=activity_type.id if activity_type else False,
                    summary='Post WIP Error',
                    note=str(e),
                    user_id=mrp_id.user_id.id if mrp_id.user_id else self.env.user.id
                )
