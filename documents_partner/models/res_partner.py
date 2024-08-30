# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "documents.mixin"]

    def _get_document_tags(self):
        company = self.company_id or self.env.company
        return company.partner_tags

    def _get_document_folder(self):
        company = self.company_id or self.env.company
        return company.partner_folder

    def _check_create_documents(self):
        company = self.company_id or self.env.company
        return company.documents_partner_settings and super()._check_create_documents()
