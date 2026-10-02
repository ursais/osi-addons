# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class FSMMobileFeatureMapping(models.Model):
    _name = "fsm.mobile.feature.mapping"
    _description = "FSM Mobile Feature Mapping"

    name = fields.Char(string="Mapping Name")
    installed_module_ids = fields.Many2many(
        "ir.module.module",
        string="Installed Modules",
        domain=[("state", "=", "installed")],
    )
    feature_line_ids = fields.One2many(
        "fsm.mobile.feature.line", "feature_id", string="Mobile Feature Lines"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id.id,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active")],
        default="draft",
    )

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name

    def set_to_draft(self):
        for rec in self:
            rec.state = "draft"

    def set_to_active(self):
        record = self.search([("state", "=", "active")])
        if record:
            raise UserError(
                self.env._(
                    "Active record is already exits in FSM Mobile Feature Mapping!"
                )
            )
        for rec in self:
            rec.state = "active"

    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_active(self):
        if any(rec.state == "active" for rec in self):
            raise UserError(
                self.env._(
                    "You can't delete FSM Mobile Feature Mapping which is in"
                    " an active state!"
                )
            )

    @api.model
    def get_fsm_mobile_feature_mapping_values(self, user_id=None):
        """Return feature mapping for the current session user.

        ``user_id`` is accepted for API compatibility but ignored so callers
        cannot probe another user's feature codes. Portal workers cannot read
        ``res.groups``; group intersection uses a targeted ``sudo()``.
        """
        user = self.env.user
        fsm_feature_mapping_rec = self.env["fsm.mobile.feature.mapping"].search(
            [("state", "=", "active")], limit=1
        )
        params_dict = {}
        feature_mapping_list = []
        installed_modules_list = []
        user_groups = user.group_ids
        for f_line_rec in fsm_feature_mapping_rec.feature_line_ids:
            matched_groups = f_line_rec.sudo().group_ids & user_groups
            if matched_groups:
                feature_mapping_list.append(
                    {
                        "id": f_line_rec.id,
                        "name": f_line_rec.name,
                        "group_ids": matched_groups.ids,
                        "code": f_line_rec.code,
                    }
                )
        for inst_module in fsm_feature_mapping_rec.sudo().installed_module_ids:
            installed_modules_list.append(
                {"id": inst_module.id, "name": inst_module.name}
            )
        if feature_mapping_list and installed_modules_list:
            params_dict.update(
                {
                    "feature_mapping": feature_mapping_list,
                    "installed_modules": installed_modules_list,
                }
            )
        return params_dict
