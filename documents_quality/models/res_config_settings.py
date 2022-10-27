# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Quality Control Points
    documents_quality_point_settings = fields.Boolean(
        related="company_id.documents_quality_point_settings",
        readonly=False,
        string="Quality Control Points",
    )
    quality_point_folder = fields.Many2one(
        "documents.folder",
        related="company_id.quality_point_folder",
        readonly=False,
        string="Quality Control Points Default Workspace",
    )
    quality_point_tags = fields.Many2many(
        "documents.tag",
        "quality_point_tags_table",
        related="company_id.quality_point_tags",
        readonly=False,
        string="Quality Control Points Tags",
    )

    @api.onchange("quality_point_folder")
    def on_quality_point_folder_change(self):
        if self.quality_point_folder != self.quality_point_tags.mapped("folder_id"):
            self.quality_point_tags = False

    # Quality Checks
    documents_quality_check_settings = fields.Boolean(
        related="company_id.documents_quality_check_settings",
        readonly=False,
        string="Quality Checks",
    )
    quality_check_folder = fields.Many2one(
        "documents.folder",
        related="company_id.quality_check_folder",
        readonly=False,
        string="Quality Checks Default Workspace",
    )
    quality_check_tags = fields.Many2many(
        "documents.tag",
        "quality_check_tags_table",
        related="company_id.quality_check_tags",
        readonly=False,
        string="Quality Checks Tags",
    )

    @api.onchange("quality_check_folder")
    def on_quality_check_folder_change(self):
        if self.quality_check_folder != self.quality_check_tags.mapped("folder_id"):
            self.quality_check_tags = False

    # Quality Alerts
    documents_quality_alert_settings = fields.Boolean(
        related="company_id.documents_quality_alert_settings",
        readonly=False,
        string="Quality Alerts",
    )
    quality_alert_folder = fields.Many2one(
        "documents.folder",
        related="company_id.quality_alert_folder",
        readonly=False,
        string="Quality Alerts Default Workspace",
    )
    quality_alert_tags = fields.Many2many(
        "documents.tag",
        "quality_alert_tags_table",
        related="company_id.quality_alert_tags",
        readonly=False,
        string="Quality Alerts Tags",
    )

    @api.onchange("quality_alert_folder")
    def on_quality_alert_folder_change(self):
        if self.quality_alert_folder != self.quality_alert_tags.mapped("folder_id"):
            self.quality_alert_tags = False
