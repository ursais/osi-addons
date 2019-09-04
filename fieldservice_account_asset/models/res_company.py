# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _default_asset_location_id(self):
        return self.env.ref('fieldservice_account_asset.asset_location')

    asset_location_id = fields.Many2one(
        'stock.location',
        string='Asset Location',
        domain="[('usage', '=', 'inventory')]",
        default=lambda self: self._default_asset_location_id())
