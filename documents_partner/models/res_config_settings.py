# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_vendor_settings = fields.Boolean(
        related="company_id.documents_vendor_settings",
        readonly=False,
        string="Vendors",
    )
    vendor_folder = fields.Many2one(
        "documents.folder",
        related="company_id.vendor_folder",
        readonly=False,
        string="Vendors Default Workspace",
    )
    vendor_tags = fields.Many2many(
        "documents.tag",
        "vendor_tags_table",
        related="company_id.vendor_tags",
        readonly=False,
        string="Vendors Tags",
    )

    @api.onchange("vendor_folder")
    def on_vendor_folder_change(self):
        if self.vendor_folder != self.vendor_tags.mapped("folder_id"):
            self.vendor_tags = False
