# Copyright (C) 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    rma_id = fields.Many2one(
        comodel_name="rma.order", string="RMA", ondelete="set null"
    )
    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA line", ondelete="set null"
    )

    @api.model
    def _get_rule(self, product_id, location_id, values):
        """Ensure that the selected rule is valid for RMAs"""
        res = super()._get_rule(product_id, location_id, values)
        rma_route_check = self.env.context.get("rma_route_check")
        if rma_route_check:
            if res and not res.route_id.rma_selectable:
                raise ValidationError(
                    _(
                        "No rule found for this product %(product)s and "
                        "location %(location)s that is valid for RMA operations."
                    )
                    % {
                        "product": product_id.default_code or product_id.name,
                        "location": location_id.complete_name,
                    }
                )
            # Don't enforce check on any chained moves
            rma_route_check.clear()
        return res
