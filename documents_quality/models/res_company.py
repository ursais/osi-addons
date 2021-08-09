# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    # Quality Control Points
    documents_quality_point_settings = fields.Boolean()
    quality_point_folder = fields.Many2one(
        "documents.folder",
        string="Quality Control Points Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_quality_point_folder", raise_if_not_found=False
        ),
    )
    quality_point_tags = fields.Many2many("documents.tag", "quality_point_tags_table")

    # Quality Checks
    documents_quality_check_settings = fields.Boolean()
    quality_check_folder = fields.Many2one(
        "documents.folder",
        string="Quality Checks Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_quality_check_folder", raise_if_not_found=False
        ),
    )
    quality_check_tags = fields.Many2many("documents.tag", "quality_check_tags_table")

    # Quality Alerts
    documents_quality_alert_settings = fields.Boolean()
    quality_alert_folder = fields.Many2one(
        "documents.folder",
        string="Quality Alerts Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_quality_alert_folder", raise_if_not_found=False
        ),
    )
    quality_alert_tags = fields.Many2many("documents.tag", "quality_alert_tags_table")
