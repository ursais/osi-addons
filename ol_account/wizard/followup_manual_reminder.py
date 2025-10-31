from odoo import _, api, models
from odoo.exceptions import UserError


class FollowupManualReminder(models.TransientModel):
    _inherit = "account_followup.manual_reminder"

    @api.depends("template_id")
    def _compute_email_recipient_ids(self):
        for wizard in self:
            partner = wizard.partner_id
            template = wizard.template_id

            wizard.email_recipient_ids = partner._get_all_followup_contacts()

    def process_followup(self):
        options = self._get_wizard_options()
        for wizard in self:
            if options.get("email"):
                followup_contacts = self.env["res.partner"].search(
                    [
                        ("id", "child_of", wizard.partner_id.id),
                        ("followup", "=", True),
                    ]
                )
                if not followup_contacts:
                    raise UserError(
                        _(
                            """No ‘Followup’ contacts are found for %s, """
                            """please add or set the ‘Followup’ setting on a contact and try again.""",
                            wizard.partner_id.display_name,
                        )
                    )
        return super().process_followup()
