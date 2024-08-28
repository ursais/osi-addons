# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_partner_settings = fields.Boolean(
        related="company_id.documents_partner_settings",
        readonly=False,
        string="Partners",
    )
    partner_folder = fields.Many2one(
        "documents.folder",
        related="company_id.partner_folder",
        readonly=False,
        string="Partners Default Workspace",
    )
    partner_tags = fields.Many2many(
        "documents.tag",
        "partner_tags_table",
        related="company_id.partner_tags",
        readonly=False,
        string="Partners Tags",
    )

    @api.onchange("partner_folder")
    def on_partner_folder_change(self):
        if self.partner_folder != self.partner_tags.mapped("folder_id"):
            self.partner_tags = False
