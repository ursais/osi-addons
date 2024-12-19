# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 by frePPLe bv
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

from odoo import models, fields, api


class WorkorderSecondaryWorkcenter(models.Model):
    _name = "mrp.workorder.secondary.workcenter"
    _description = "Secondary workcenter of a work order"
    _rec_name = "workcenter_id"

    workorder_id = fields.Many2one(
        "mrp.workorder",
        "Parent work order",
        index=True,
        ondelete="cascade",
        required=True,
    )
    workcenter_id = fields.Many2one(
        "mrp.workcenter",
        "Work Center",
        required=True,
        ondelete="cascade",
    )
    duration = fields.Float("Duration", help="time in minutes")

    @api.onchange("duration")
    def _onchange_duration(self):
        self.workorder_id.duration_expected = self.workorder_id._get_duration_expected()
