# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MRPWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    cost_already_recorded = fields.Boolean(
        "Cost Recorded",
        help="Technical field automatically checked when a ongoing production "
        "posts journal entries for its costs. This way, we can record one "
        "production's cost multiple times and only consider new entries "
        "in the work centers time lines.",
    )
