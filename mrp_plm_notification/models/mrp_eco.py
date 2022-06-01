# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MrpEcoStage(models.Model):
    _inherit = "mrp.eco.stage"

    template_id = fields.Many2one(
        "mail.template",
        "Email Template",
        domain="[('model', '=', 'mrp.eco')]",
        help="Automated send email when the ECO reaches this stage.",
    )


class MrpEco(models.Model):
    _name = "mrp.eco"
    _inherit = ["mrp.eco", "mail.thread.cc", "mail.activity.mixin"]

    def _track_template(self, changes):
        res = super(MrpEco, self)._track_template(changes)
        eco = self[0]
        if "stage_id" in changes and eco.stage_id.template_id:
            res["stage_id"] = (
                eco.stage_id.template_id,
                {
                    "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"].xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res
