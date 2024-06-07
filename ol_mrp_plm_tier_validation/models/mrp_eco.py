# Import Odoo libs
from odoo import fields, models


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

    # END #######

    def write(self, vals):
        # Tier Validation does not work with Stages, only States :-(
        # Workaround is to signal state transition adding it to the write values
        if "stage_id" in vals:
            stage_id = vals.get("stage_id")
            stage = self.env["mrp.eco.stage"].browse(stage_id)
            vals["state"] = stage.state
        res = super().write(vals)
        if "stage_id" in vals and vals.get("stage_id") in self._state_from:
            self.restart_validation()
        return res
