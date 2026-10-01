# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_mrp_settings = fields.Boolean(
        related="company_id.documents_mrp_settings",
        readonly=False,
        string="Manufacturing",
    )
    mrp_folder_id = fields.Many2one(
        "documents.document",
        related="company_id.mrp_folder_id",
        readonly=False,
        string="Manufacturing default folder",
    )
    mrp_tag_ids = fields.Many2many(
        "documents.tag",
        related="company_id.mrp_tag_ids",
        readonly=False,
        string="Manufacturing Tags",
    )
