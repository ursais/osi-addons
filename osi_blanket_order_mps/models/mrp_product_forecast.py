# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpProductForecast(models.Model):
    _inherit = "mrp.product.forecast"

    is_edit_forcast_qty = fields.Boolean(defaul=False)
