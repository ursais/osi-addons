# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production", "documents.mixin"]

    def _get_document_vals_access_rights(self):
        return {
            "access_internal": "view",
            "access_via_link": "view",
        }

    def _get_document_owner(self):
        return self.env.user

    def _get_document_tags(self):
        company = self.company_id or self.env.company
        return company.mrp_tag_ids

    def _get_document_folder(self):
        company = self.company_id or self.env.company
        return company.mrp_folder_id

    def _check_create_documents(self):
        company = self.company_id or self.env.company
        return company.documents_mrp_settings and super()._check_create_documents()
