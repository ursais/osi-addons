# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 by frePPLe bv
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

from itertools import chain
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WorkOrderInherit(models.Model):
    _inherit = "mrp.workorder"

    secondary_workcenters = fields.One2many(
        "mrp.workorder.secondary.workcenter",
        "workorder_id",
        required=False,
        copy=True,
        help="Extra workcenters needed for this work order",
    )

    def assign_secondary_work_centers(self):
        """
        Logic to assign secondary work centers:
        - if the work center has no children:
            create wo_sec_line record for this workcenter
        - else if its a tool and another wo of this mo uses a secondary workcenter already
          of same group and same skill:
            use the same secondary as the other work order
        - else if a skill is required:
            find child a child resource that has the correct skill, ordered by priority
        - else:
            take the first child, ordered by name
        """
        # if secondary workcenters are already set, assure the duration is correct
        secondary_workcenters_values = []
        if self.secondary_workcenters:
            for i in self.secondary_workcenters:
                for x in self.operation_id.secondary_workcenter:
                    if (
                        x.workcenter_id.id == i.workcenter_id.id
                        or x.workcenter_id.id == i.workcenter_id.owner.id
                    ):
                        secondary_workcenters_values.append(
                            [(0, 0, {"duration", x.duration * self.qty_production})]
                        )
                        break
            if secondary_workcenters_values:
                self.secondary_workcenters = secondary_workcenters_values
            return True

        for x in self.operation_id.secondary_workcenter:

            # store the ids of the workcenters having that secondary workcenter as owner
            children = [
                i.id
                for i in self.env["mrp.workcenter"].search(
                    [("owner", "=", x.workcenter_id.id)], order="name"
                )
            ]

            selectedWorkCenter = None
            if not children:
                selectedWorkCenter = x.workcenter_id.id

            if not selectedWorkCenter and (
                x.workcenter_id.tool
                or self.env["mrp.workcenter"].search_count(
                    [("owner", "=", x.workcenter_id.id), ("tool", "=", True)]
                )
                > 0
            ):
                # check if another wo of the same MO already has already selected a
                # tool workcenter for the same skill
                for wo in self.production_id.workorder_ids:
                    if wo.id == self.id:
                        continue
                    for y in wo.operation_id.secondary_workcenter:
                        if x.skill == y.skill and x.workcenter_id == y.workcenter_id:
                            for sw in wo.secondary_workcenters:
                                if sw.workcenter_id.id in children:
                                    selectedWorkCenter = sw.workcenter_id.id
                                    break
                            break
                    if selectedWorkCenter:
                        break

            if not selectedWorkCenter:
                if x.skill and x.skill.id:
                    # Find workcenters with the required skill
                    valid_workcenters = (
                        self.env["mrp.workcenter.skill"]
                        .search(
                            [("skill", "=", x.skill.id)],
                            order="priority",
                        )
                        .read(["id", "workcenter"])
                    )
                    for v in valid_workcenters[:]:
                        if v["workcenter"][0] in children:
                            # add the secondary record with the top priority workcenter
                            selectedWorkCenter = v["workcenter"][0]
                            break
                    if not selectedWorkCenter:
                        _logger.warning(
                            "couldn't find a valid secondary work center with %s skill"
                            % (x.skill.name,)
                        )
                else:
                    # no skills, pick the first child
                    selectedWorkCenter = children[0]

            if selectedWorkCenter:
                secondary_workcenters_values.append(
                    (
                        0,
                        0,
                        {
                            "workorder_id": self.id,
                            "workcenter_id": selectedWorkCenter,
                            "duration": x.duration * self.qty_production,
                        },
                    )
                )
        if secondary_workcenters_values:
            self.secondary_workcenters = secondary_workcenters_values
        return True

    @api.model_create_multi
    def create(self, vals_list):
        wo_list = super().create(vals_list)
        if not self.env.context.get("ignore_secondary_workcenters", False):
            for wo in wo_list:
                wo.assign_secondary_work_centers()
        return wo_list

    @api.onchange("qty_producing")
    def _onchange_qty_producing(self):
        if self.secondary_workcenters:
            self.assign_secondary_work_centers()
            self.duration_expected = self._get_duration_expected()

    def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        duration = super()._get_duration_expected(alternative_workcenter, ratio)
        # get the max duration of all secondary workcenters, because this is used for top-level planning
        if self.secondary_workcenters:
            return max(
                chain(
                    [duration],
                    [
                        secondary_wc.duration
                        for secondary_wc in self.secondary_workcenters
                        if secondary_wc.duration and secondary_wc.duration > 0
                    ],
                )
            )
        else:
            return duration
