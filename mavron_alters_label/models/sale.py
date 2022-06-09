# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    mavron_model_id = fields.Many2one("product.product")
    vehicle_certification = fields.Selection([("complete", "Complete"),
                                              ("incomplete", "Incomplete")])
