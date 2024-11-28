# Import Odoo libs
from odoo import fields, models


class MrpWorkorder(models.Model):
    """Inherit Work Orders to add the batch field."""

    _inherit = "mrp.workorder"

    # COLUMNS #########

    mrp_batch_id = fields.Many2one(
        string="Batch",
        related="production_id.mrp_batch_id",
        store=True,
    )
    operation_type = fields.Selection(related="operation_id.type")

    # END #########
    # METHODS #####

    def action_mrp_workorder_dependencies(self, action_name):
        if action_name == "batch":
            # Get the action for batch, adjusting the XML ID dynamically
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "mrp_batch.action_mrp_workorder_%s" % action_name
            )

            # Get the custom view for the batch
            ref = "mrp_batch.workcenter_line_gantt_batch"
            custom_view = self.env.ref(ref).id

            # Insert the custom view as the first Gantt view
            action["views"] = [(custom_view, "gantt")] + [
                (id, kind) for id, kind in action["views"] if kind != "gantt"
            ]

            return action

        # For other action names, fallback to the original method
        return super().action_mrp_workorder_dependencies(action_name)

    # END #########
