# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api

from odoo.addons.base_geoengine import geo_model
from odoo.addons.base_geoengine import fields as geo_fields


class FSMOrder(geo_model.GeoModel):
    _inherit = 'fsm.order'

    @api.model
    def create(self, vals):
        res = super(FSMOrder, self).create(vals)
        lat = res.location_id.partner_latitude
        lng = res.location_id.partner_longitude
        if lat and lng:
            pnt = geo_fields.GeoPoint.from_latlon(cr=self.env.cr,
                                                  latitude=lat,
                                                  longitude=lng)
            res.shape = pnt
        return res

    @api.onchange('location_id')
    def onchange_location(self):
        for order in self:
            order._update_geometry()

    def _update_geometry(self):
        lat = self.location_id.partner_latitude
        lng = self.location_id.partner_longitude
        if lat and lng:
            pnt = geo_fields.GeoPoint.from_latlon(cr=self.env.cr,
                                                  latitude=lat,
                                                  longitude=lng)
            self.shape = pnt
