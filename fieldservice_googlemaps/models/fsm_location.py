# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api

from odoo.addons.base_geoengine import geo_model
from odoo.addons.base_geoengine import fields as geo_fields


class FSMLocation(geo_model.GeoModel):
    _inherit = 'fsm.location'

    @api.model
    def create(self, vals):
        res = super(FSMLocation, self).create(vals)
        lat = vals['partner_latitude']
        lng = vals['partner_longitude']
        if lat and lng:
            pnt = geo_fields.GeoPoint.from_latlon(cr=self.env.cr,
                                                  latitude=lat,
                                                  longitude=lng)
            res.shape = pnt
        return res

    def _update_order_geometries(self):
        for loc in self:
            orders = loc.env['fsm.order'].search(
                [('location_id', '=', loc.id)])
            for order in orders:
                order._update_geometry()

    @api.multi
    def write(self, vals):
        res = super(FSMLocation, self).write(vals)
        if ('partner_latitude' in vals) and ('partner_longitude' in vals):
            lat = vals['partner_latitude']
            lng = vals['partner_longitude']
            pnt = geo_fields.GeoPoint.from_latlon(cr=self.env.cr,
                                                  latitude=lat,
                                                  longitude=lng)
            self.shape = pnt
            self._update_order_geometries()
        return res
