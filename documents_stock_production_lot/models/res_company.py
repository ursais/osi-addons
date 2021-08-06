# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    documents_lot_settings = fields.Boolean()
    lot_folder = fields.Many2one(
        "documents.folder",
        string="Lot/Tracking Number Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_stock_production_lot.documents_folder_lot",
            raise_if_not_found=False,
        ),
    )
    document_lot_tags = fields.Many2many(
        "documents.tag", "document_lot_tags", string="Lot/Tracking Number Tags"
    )
