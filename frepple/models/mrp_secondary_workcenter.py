# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 by frePPLe bv
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

from odoo import models, fields


class SecondaryWorkcenter(models.Model):
    _name = "mrp.secondary.workcenter"
    _description = "List of secondary work centers"
    _rec_name = "workcenter_id"

    routing_workcenter_id = fields.Many2one(
        "mrp.routing.workcenter",
        "Parent routing workcenter",
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
    skill = fields.Many2one(
        "mrp.skill",
        "Skill",
        required=False,
        help="Workcenter skill required to perform this operation",
    )
    search_mode = fields.Selection(
        [
            ("PRIORITY", "priority"),
            ("MINCOST", "minimum cost"),
            ("MINPENALTY", "minimum penalty"),
            ("MINCOSTPENALTY", "minimum cost plus penalty"),
        ],
        string="Search Mode",
        required=False,
        default="PRIORITY",
        help="Method to choose a workcenter among alternatives",
    )
    priority = fields.Integer(
        "priority", default=1, help="Priority of this workcenter among alternatives"
    )
    duration = fields.Float("Duration", help="time in minutes")
