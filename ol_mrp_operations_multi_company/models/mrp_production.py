# Import Odoo libs
from odoo import api, models
from odoo.fields import Command


class MrpProduction(models.Model):
    """
    Override functions to enable multi-company operations.
    """

    _inherit = "mrp.production"

    # METHODS ##########

    @api.depends("bom_id", "product_id", "product_qty", "product_uom_id")
    def _compute_workorder_ids(self):
        """
        Override to generate work orders using BoM operations
        that match the MO's company or are global.
        """
        for production in self:
            if production.state != "draft":
                continue

            # Step 1: Link existing valid workorders
            workorders_list = [
                Command.link(wo.id)
                for wo in production.workorder_ids.filtered(lambda wo: wo.ids)
            ]

            if not production.bom_id:
                production.workorder_ids = workorders_list
                continue

            # Step 2: Determine relevant BoMs
            exploded_boms_data = production.bom_id.explode(
                production.product_id,
                production.product_uom_id._compute_quantity(
                    production.product_qty, production.bom_id.product_uom_id
                ),
                picking_type=production.bom_id.picking_type_id,
            )
            exploded_boms = exploded_boms_data[0]
            relevant_boms = [bom_line[0] for bom_line in exploded_boms]

            # Step 3: Remove outdated workorders
            deleted_workorders_ids = production.workorder_ids.filtered(
                lambda wo: wo.operation_id
                and wo.operation_id.bom_id not in relevant_boms
            ).ids
            workorders_list += [
                Command.delete(wo_id) for wo_id in deleted_workorders_ids
            ]

            # Step 4: Reset if BoM or product has changed
            if production.product_id != production._origin.product_id or (
                production._origin.bom_id != production.bom_id
                and production._origin.bom_id.operation_ids
                and not production.workorder_ids.filtered(
                    lambda wo: wo.ids and wo.operation_id
                )
            ):
                production.workorder_ids = [Command.clear()]

            # Step 5: Build workorders
            if (
                production.bom_id
                and production.product_id
                and production.product_qty > 0
            ):
                workorders_values = []
                for bom, bom_data in exploded_boms:
                    if not (
                        bom.operation_ids
                        and (
                            not bom_data["parent_line"]
                            or bom_data["parent_line"].bom_id.operation_ids
                            != bom.operation_ids
                        )
                    ):
                        continue

                    for operation in bom.operation_ids:
                        # Allow global or matching-company operations and workcenters
                        if (
                            operation.company_id
                            and operation.company_id != production.company_id
                        ):
                            continue
                        if (
                            operation.workcenter_id.company_id
                            and operation.workcenter_id.company_id
                            != production.company_id
                        ):
                            continue
                        if operation._skip_operation_line(bom_data["product"]):
                            continue

                        workorders_values.append(
                            {
                                "name": operation.name,
                                "production_id": production.id,
                                "workcenter_id": operation.workcenter_id.id,
                                "product_uom_id": production.product_uom_id.id,
                                "operation_id": operation.id,
                                "state": "pending",
                            }
                        )

                # Step 6: Reuse existing workorders if possible
                workorders_dict = {
                    wo.operation_id.id: wo
                    for wo in production.workorder_ids.filtered(
                        lambda wo: wo.operation_id
                        and wo.ids
                        and wo.id not in deleted_workorders_ids
                    )
                }

                for values in workorders_values:
                    existing = workorders_dict.get(values["operation_id"])
                    if existing:
                        workorders_list += [Command.update(existing.id, values)]
                    else:
                        workorders_list += [Command.create(values)]

                production.workorder_ids = workorders_list
            else:
                # Step 7: Clear workorders if no valid operations remain
                production.workorder_ids = [
                    Command.delete(wo.id)
                    for wo in production.workorder_ids.filtered(
                        lambda wo: wo.ids and wo.operation_id
                    )
                ]

    def _link_bom(self, bom):
        """
        Override to exclude BoM operations not matching the MO's company.
        This ensures that `action_update_bom` doesn't pull in operations
        from the wrong company.
        """

        def _filter_valid_operations(operation):
            return (
                not operation.company_id or operation.company_id == self.company_id
            ) and (
                not operation.workcenter_id.company_id
                or operation.workcenter_id.company_id == self.company_id
            )

        # Rebuild filtered operations in memory and patch on the bom
        bom = bom.with_prefetch(bom.ids)
        bom.operation_ids = bom.operation_ids.filtered(_filter_valid_operations)

        return super()._link_bom(bom)

    # END #########
