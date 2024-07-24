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

    # END #######

    def write(self, vals):
        """Base Tier Validation does not work with Stages, only States :-(
        The base_tier_validation uses the 'state' field on classes, the states are
        defined in _state_from and _state_to in order to trigger the validation checks.
        Workaround is to signal state transition adding it to the write values"""
        if "stage_id" in vals:
            stage_id = vals.get("stage_id")
            stage = self.env["mrp.eco.stage"].browse(stage_id)
            current_state = self.state
            current_stage = self.stage_id
            to_next_stage = current_stage.sequence < stage.sequence
            if to_next_stage and stage.approval_state:
                vals["state"] = "approved"
        res = super().write(vals)
        if "stage_id" in vals:
            to_next_stage = current_stage.sequence < stage.sequence
            if to_next_stage:
                self.state = current_state
            # if vals.get("state") in self._state_from:
            #     # If stage is being written and is in the _state_from then that means
            #     # validations need to be reset so trigger the restart_validation method,
            #     # contained in base_tier_validation and clears reviews.
            #     self.restart_validation()
        return res

    @api.depends("stage_id")
    def _compute_prev_next_stage(self):
        for rec in self:
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

    def action_move_to_prev_stage(self):
        for rec in self:
            rec.restart_validation()
            rec.write({"stage_id": rec.prev_stage_id.id})

    def action_move_to_next_stage(self):
        for rec in self:
            rec.write({"stage_id": rec.next_stage_id.id})
