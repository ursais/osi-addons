# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asset_location_id = fields.Many2one(
        string='Asset Location',
        related='company_id.asset_location_id',
        readonly=False)
