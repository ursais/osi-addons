# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    documents_lot_settings = fields.Boolean(
        related="company_id.documents_lot_settings",
        readonly=False,
        string="Lot",
    )
    lot_folder = fields.Many2one(
        "documents.folder",
        related="company_id.lot_folder",
        readonly=False,
        string="Lot Default Workspace",
    )
    lot_tags = fields.Many2many(
        "documents.tag",
        "document_lot_tag",
        related="company_id.document_lot_tags",
        readonly=False,
        string="Lot Tags",
    )

    @api.onchange("lot_folder")
    def _onchange_lot_folder(self):
        if self.lot_folder != self.lot_tags.mapped("folder_id"):
            self.lot_tags = False
