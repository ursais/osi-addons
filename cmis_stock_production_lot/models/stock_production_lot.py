# Copyright (C) 2018 - TODAY, Open Source Integrators


from odoo import models
from odoo.addons.cmis_field import fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    cmis_folder = fields.CmisFolder(
        copy=False,
        create_name_get='_cmis_create_name_get',
        create_parent_get='_cmis_create_parent_get',
        oldname='cmis_objectid')

    @api.multi
    def _cmis_create_name_get(self, field, backend):
        ret = {}
        for record in self:
            ret[record.id] = record.name or ''
        return ret

    @api.multi
    def _cmis_create_parent_get(self, field, backend):
        ret = {}
        path_parts = [backend.initial_directory_write, 'cmis']
        parent_cmis_objectid = backend.get_folder_by_path_parts(
            path_parts, create_if_not_found=True)
        for record in self:
            ret[record.id] = parent_cmis_objectid
        return ret
