# Import Odoo libs
from odoo import api, fields, models


class MrpEco(models.Model):
    """
    Add tier validation to PLM ECOs
    """

    _name = "mrp.eco"
    _inherit = ["mrp.eco", "tier.validation"]
    _state_from = [
        "confirmed",
        "progress",
        "rebase",
        "conflict",
    ]
    _state_to = ["done", "approved"]
    _cancel_state = ["cancel"]
    _tier_validation_manual_config = False

    # COLUMNS ###

    state = fields.Selection(
        selection_add=[
            ("approved", "Approved"),
            ("cancel", "Canceled"),
        ],
        ondelete={"approved": "cascade", "cancel": "cascade"},
    )
    tier_review_history_ids = fields.One2many(
        comodel_name="tier.validation.history",
        inverse_name="eco_id",
        string="Tier Validation History",
    )
    prev_stage_id = fields.Many2one(
        comodel_name="mrp.eco.stage",
        compute="_compute_prev_next_stage",
        store=True,
        string="Previous Stage",
    )
    next_stage_id = fields.Many2one(
        comodel_name="mrp.eco.stage",
        compute="_compute_prev_next_stage",
        store=True,
        string="Next Stage",
    )
    stage_canceled_on = fields.Many2one(
        comodel_name="mrp.eco.stage",
        store=True,
        string="Stage Canceled On",
    )

    # END #######

    def write(self, vals):
        """
        Override the write method to handle state transitions based on stage changes.
        Base Tier Validation does not work with Stages, only States :-(
        The base_tier_validation uses the 'state' field on classes, the states are
        defined in _state_from and _state_to in order to trigger the validation checks.
        Workaround is to signal state transition adding it to the write values but we
        only care to change the state if the new stage is set as an approval stage.
        We set the state back afterwards to so it's ready for the next stage change."""
        if "stage_id" in vals:
            # Get the new stage based on the 'stage_id' value
            new_stage_id = self.env["mrp.eco.stage"].browse(vals.get("stage_id"))
            # Store the current state
            current_state = self.state
            # Determine if the transition is to the next stage
            to_next_stage = self.stage_id.sequence < new_stage_id.sequence
            approved = False

            # If the 'state' is not in vals, and we are transitioning to the next stage
            # and the new stage requires approval, set the state to 'approved' to
            # trigger the base tier valdionation state change methods to check for
            # tier validation
            if "state" not in vals and to_next_stage and new_stage_id.is_approval_stage:
                vals["state"] = "approved"
                approved = True

            # If going to canceled stage, save current stage so we can return
            if new_stage_id.cancel_stage:
                vals["stage_canceled_on"] = self.stage_id.id

            # Call the super class's write method with the modified vals
            res = super().write(vals)

            # If we transitioned to the next stage and set the state to approved,
            # restore the original state
            if to_next_stage and approved:
                self.state = current_state
        else:
            # If 'stage_id' is not in vals, just call the super class's write method
            res = super().write(vals)

        return res

    @api.depends("stage_id")
    def _compute_prev_next_stage(self):
        for rec in self:
            if not rec.stage_id.cancel_stage:
                stages = self.env["mrp.eco.stage"].search(
                    [
                        ("type_ids", "in", rec.type_id.ids),
                        ("company_id", "=", rec.company_id.id),
                    ]
                )
                prev_stage = stages.filtered(
                    lambda stage: stage.sequence < rec.stage_id.sequence
                )
                next_stage = stages.filtered(
                    lambda stage: stage.sequence > rec.stage_id.sequence
                )
                rec.prev_stage_id = (
                    prev_stage and max(prev_stage, key=lambda s: s.sequence).id or False
                )
                rec.next_stage_id = (
                    next_stage and min(next_stage, key=lambda s: s.sequence).id or False
                )
            else:
                rec.prev_stage_id = rec.stage_canceled_on.id
                rec.next_stage_id = rec.stage_canceled_on.id

    def action_move_to_prev_stage(self):
        for rec in self:
            rec.restart_validation()
            rec.write({"stage_id": rec.prev_stage_id.id})

    def action_move_to_next_stage(self):
        for rec in self:
            rec.write({"stage_id": rec.next_stage_id.id})

    def action_new_revision(self):
        res = super(MrpEco, self).action_new_revision()
        for rec in self:            
            rec.write({"stage_id": rec.next_stage_id.id})
        return res
