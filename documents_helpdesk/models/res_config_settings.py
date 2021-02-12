# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


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
        "hepldesk.tag",
        related="company_id.document_helpdesk_tags",
        readonly=False,
        string="Helpdesk Tags",
    )
