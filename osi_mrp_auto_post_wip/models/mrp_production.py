# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    def _cron_process_action_post_inventory_wip(self):
        mrp_ids = self.env["mrp.production"].search(
            [("state", "in", ["progress", "to_close"])]
        )
        mrp_ids.action_post_inventory_wip()
