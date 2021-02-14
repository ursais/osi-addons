# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_helpdesk_settings = fields.Boolean(
        related="company_id.documents_helpdesk_settings",
        readonly=False,
        string="Helpdesk",
    )
    helpdesk_folder = fields.Many2one(
        "documents.folder",
        related="company_id.helpdesk_folder",
        readonly=False,
        string="Helpdesk Default Workspace",
    )
    helpdesk_tags = fields.Many2many(
        "documents.tag",
        "document_helpdesk_tag",
        related="company_id.document_helpdesk_tags",
        readonly=False,
        string="Helpdesk Tags",
    )

    @api.onchange("helpdesk_folder")
    def on_helpdesk_folder_change(self):
        if self.helpdesk_folder != self.helpdesk_tags.mapped("folder_id"):
            self.helpdesk_tags = False
