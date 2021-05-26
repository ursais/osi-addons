# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRequest(models.Model):
    _inherit = "stock.request"

    @api.model
    def create(self, vals):
        # Do nothing if analylic account is already set
        if not vals.get("analytic_account_id", False):
            # Get our ticket
            if vals.get("helpdesk_ticket_id", False):
                ticket_id = self.env["helpdesk.ticket"].browse(
                    vals.get("helpdesk_ticket_id")
                )
                # Check ticket for Location
                if ticket_id.fsm_location_id:
                    # Check Location for Analytic Account
                    if ticket_id.fsm_location_id.analytic_account_id:
                        vals.update(
                            {
                                "analytic_account_id": ticket_id.fsm_location_id.analytic_account_id.id
                            }
                        )
        return super().create(vals)
