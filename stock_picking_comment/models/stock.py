# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    comment = fields.Text('Comment')
