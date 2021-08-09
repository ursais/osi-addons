# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_elearning_settings = fields.Boolean(
        related="company_id.documents_elearning_settings",
        readonly=False,
        string="Elearning",
    )
    elearning_folder = fields.Many2one(
        "documents.folder",
        related="company_id.elearning_folder",
        readonly=False,
        string="Elearning Default Workspace",
    )
    elearning_tags = fields.Many2many(
        "documents.tag",
        "elearning_tags_table",
        related="company_id.elearning_tags",
        readonly=False,
        string="Elearning Tags",
    )

    @api.onchange("elearning_folder")
    def on_elearning_folder_change(self):
        if self.elearning_folder != self.elearning_tags.mapped("folder_id"):
            self.elearning_tags = False
