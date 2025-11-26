# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleOrder(models.Model):
    """
    Extends the sale.order model to add a test field.

    This model adds a test_field (string) to sale orders for testing purposes.
    """
    _inherit = "sale.order"

    test_field = fields.Char(
        string="Test Field",
        help="Test field for sale order customization",
        tracking=True,
    )
