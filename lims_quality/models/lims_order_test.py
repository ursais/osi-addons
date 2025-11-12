# Copyright (C) 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class LimsOrderTest(models.Model):
    _inherit = "lims.order.test"

    quality_control_point_id = fields.Many2one(
        "quality.point", string="Quality Control Point"
    )
    quality_check_id = fields.Many2one("quality.check", string="Quality Check")
