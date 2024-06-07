# Copyright (C) 2024, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MrpProduction(models.Model):
    _inherit = ["mrp.production", "base.exception"]
    _name = "mrp.production"

    @api.model
    def test_all_archived_finish_product(self):
        mrp_set = self.search([("product_id.active", "=", False)])
        mrp_set.detect_exceptions()
        return True

    @api.model
    def _reverse_field(self):
        return "production_ids"

    def detect_exceptions(self):
        all_exceptions = super().detect_exceptions()
        components = self.mapped("move_raw_ids")
        all_exceptions += components.detect_exceptions()
        return all_exceptions

    @api.constrains("ignore_exception", "move_raw_ids", "product_id")
    def mrp_check_exception(self):
        mrp_orders = self.filtered(lambda s: not s.product_id.active)
        if mrp_orders:
            mrp_orders._check_exception()

    @api.onchange("move_raw_ids")
    def onchange_ignore_exception(self):
        for line in self.move_raw_ids:
            if not line.product_id.active:
                line.ignore_exception = False

    def action_confirm(self):
        for rec in self:
            if rec.detect_exceptions() and not rec.ignore_exception:
                return rec._popup_exceptions()
        return super().action_confirm()

    @api.model
    def _get_popup_action(self):
        action = self.env.ref("mrp_exception.action_mrp_exception_confirm")
        return action
