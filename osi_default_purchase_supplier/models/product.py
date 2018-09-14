# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    generic_flag = fields.Boolean(
        string='Generic',
        default=False,
        copy=False,
        track_visibility='onchange'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    generic_flag = fields.Boolean(
        string="Generic",
        default=False,
        copy=False,
        track_visibility='onchange'
    )
