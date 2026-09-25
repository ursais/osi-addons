# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models
from odoo.fields import Domain


class ResCompany(models.Model):
    _inherit = "res.company"

    documents_lot_settings = fields.Boolean()
    lot_folder_id = fields.Many2one(
        "documents.document",
        string="Lot/Tracking Number Folder",
        check_company=True,
        compute="_compute_lot_folder_id",
        store=True,
        readonly=False,
        domain=[("type", "=", "folder"), ("shortcut_document_id", "=", False)],
    )
    lot_tag_ids = fields.Many2many(
        "documents.tag", "document_lot_tags", string="Lot/Tracking Number Tags"
    )

    @api.depends("documents_lot_settings")
    def _compute_lot_folder_id(self):
        folder_id = self.env.ref(
            "documents_stock_production_lot.documents_folder_lot",
            raise_if_not_found=False,
        )
        self._reset_default_documents_folder_id(
            "documents_lot_settings", "lot_folder_id", folder_id
        )

    def _get_used_folder_ids_domain(self, folder_ids):
        return super()._get_used_folder_ids_domain(folder_ids) | (
            Domain("lot_folder_id", "in", folder_ids)
            & Domain("documents_lot_settings", "=", True)
        )
