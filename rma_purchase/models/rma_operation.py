# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    purchase_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
        ],
        default="no",
    )

    @api.constrains("purchase_policy")
    def _check_purchase_policy(self):
        if self.filtered(lambda r: r.purchase_policy != "no" and r.type != "supplier"):
            raise ValidationError(
                _("Purchase Policy can only apply to supplier operations")
            )
