# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class StockProductionLot(models.Model):
    _name = "stock.production.lot"
    _inherit = ["stock.production.lot", "documents.mixin"]

    def _get_document_folder(self):
        return self.company_id.lot_folder

    def _get_document_tags(self):
        company = self.company_id or self.env.company
        return company.document_lot_tags

    def _check_create_documents(self):
        company = self.company_id or self.env.company
        return company.documents_lot_settings and super()._check_create_documents()
