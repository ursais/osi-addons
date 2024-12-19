# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    manufacturing_warehouse = fields.Many2one(
        "stock.warehouse",
        "Manufacturing warehouse",
        related="company_id.manufacturing_warehouse",
        readonly=False,
    )
    calendar = fields.Many2one(
        "resource.calendar",
        "Calendar",
        related="company_id.calendar",
        readonly=False,
    )
    webtoken_key = fields.Char(
        "Webtoken key", size=128, related="company_id.webtoken_key", readonly=False
    )
    frepple_server = fields.Char(
        "frePPLe server", size=128, related="company_id.frepple_server", readonly=False
    )
    respect_reservations = fields.Boolean(
        related="company_id.respect_reservations", readonly=False
    )
    disclose_stack_trace = fields.Boolean(
        related="company_id.disclose_stack_trace",
        readonly=False,
    )
