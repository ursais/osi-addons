# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models
from odoo.fields import Domain


class ResCompany(models.Model):
    _inherit = "res.company"

    documents_purchase_settings = fields.Boolean()
    purchase_folder_id = fields.Many2one(
        "documents.document",
        string="Purchase Folder",
        check_company=True,
        compute="_compute_purchase_folder_id",
        store=True,
        readonly=False,
        domain=[("type", "=", "folder"), ("shortcut_document_id", "=", False)],
    )
    purchase_tag_ids = fields.Many2many("documents.tag", "purchase_tags_table")

    @api.depends("documents_purchase_settings")
    def _compute_purchase_folder_id(self):
        folder_id = self.env.ref(
            "documents_purchase.documents_purchase_folder", raise_if_not_found=False
        )
        self._reset_default_documents_folder_id(
            "documents_purchase_settings", "purchase_folder_id", folder_id
        )

    def _get_used_folder_ids_domain(self, folder_ids):
        return super()._get_used_folder_ids_domain(folder_ids) | (
            Domain("purchase_folder_id", "in", folder_ids)
            & Domain("documents_purchase_settings", "=", True)
        )
