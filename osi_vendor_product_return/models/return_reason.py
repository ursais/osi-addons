# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ReturnReason(models.Model):
    _name = "return.reason"
    _description = "Return Reason code"

    name = fields.Char(required=True, copy=False, index=True)
