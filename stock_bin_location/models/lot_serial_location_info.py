# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class LotSerialLocationInfo(models.TransientModel):
    _inherit = "lot.serial.location.info"

    bin_location = fields.Char(related="lot_id.bin_location", string="Bin Location")
