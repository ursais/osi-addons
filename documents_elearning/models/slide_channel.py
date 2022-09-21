# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class SlideChannel(models.Model):
    _name = "slide.channel"
    _inherit = ["slide.channel", "documents.mixin"]

    def _get_document_tags(self):
        company = self.env.company
        return company.elearning_tags

    def _get_document_folder(self):
        company = self.env.company
        return company.elearning_folder

    def _check_create_documents(self):
        company = self.env.company
        return (
            company.documents_elearning_settings and super()._check_create_documents()
        )
