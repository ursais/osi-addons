# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class QualityCheck(models.Model):
    _name = "quality.check"
    _inherit = ["quality.check", "documents.mixin"]

    def _get_document_tags(self):
        company = self.company_id or self.env.company
        return company.quality_check_tags

    def _get_document_folder(self):
        company = self.company_id or self.env.company
        return company.quality_check_folder

    def _check_create_documents(self):
        company = self.company_id or self.env.company
        return (
            company.documents_quality_check_settings
            and super()._check_create_documents()
        )
