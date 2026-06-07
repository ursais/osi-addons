# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    """
    Extends the sale.order model to add fleet vehicle functionality.

    This model adds the ability to:
    - Link sale orders to specific fleet vehicles
    - Track which vehicle is associated with each sale order
    - Enable filtering and reporting by vehicle

    Note: This module is designed to be compatible with Odoo 18+.
    """

    _inherit = "sale.order"

    # Many2one field to link sale orders to fleet vehicles
    # This field enables linking sale orders to fleet vehicles for tracking
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        copy=False,  # Don't copy when duplicating sale orders
        help="Fleet vehicle associated with this sale order",
        tracking=True,  # Track changes for audit purposes
    )
