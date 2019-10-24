# Copyright (C) 2018 - TODAY, Brian McMaster
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMLocation(models.Model):
    _inherit = 'fsm.location'

    default_warehouse_id = fields.Many2one('stock.warehouse',
                                           string="Default Warehouse")
