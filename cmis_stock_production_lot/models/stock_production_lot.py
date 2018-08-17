# -*- coding: utf-8 -*-
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
