# Import Odoo libs
from odoo import _, api, models
from odoo.exceptions import ValidationError


class MrpEco(models.Model):
    """Inherit ECO to add substate methods."""

    _inherit = ["mrp.eco", "base.substate.mixin"]
    _name = "mrp.eco"

    # METHODS ##########

    @api.constrains("substate_id", "state")
    def check_substate_id_value(self):
        sale_states = dict(self._fields["state"].selection)
        for eco in self:
            target_state = eco.substate_id.target_state_value_id.target_state_value
            if eco.substate_id and eco.state != target_state:
                raise ValidationError(
                    _(
                        "The substate %(name)s is not defined for the state"
                        " %(state)s but for %(target_state)s "
                    )
                    % {
                        "name": eco.substate_id.name,
                        "state": _(sale_states[eco.state]),
                        "target_state": _(sale_states[target_state]),
                    }
                )

    def _track_template(self, changes):
        res = super()._track_template(changes)
        track = self[0]
        if "substate_id" in changes and track.substate_id.mail_template_id:
            res["substate_id"] = (
                track.substate_id.mail_template_id,
                {
                    "composition_mode": "comment",
                    "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res

    # END #########
