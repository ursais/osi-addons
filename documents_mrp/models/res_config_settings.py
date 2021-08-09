# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_mrp_settings = fields.Boolean(
        related="company_id.documents_mrp_settings",
        readonly=False,
        string="Manufacturing",
    )
    mrp_folder = fields.Many2one(
        "documents.folder",
        related="company_id.mrp_folder",
        readonly=False,
        string="Manufacturing Default Workspace",
    )
    mrp_tags = fields.Many2many(
        "documents.tag",
        "mrp_tags_table",
        related="company_id.mrp_tags",
        readonly=False,
        string="Manufacturing Tags",
    )

    @api.onchange("mrp_folder")
    def on_mrp_folder_change(self):
        if self.mrp_folder != self.mrp_tags.mapped("folder_id"):
            self.mrp_tags = False
