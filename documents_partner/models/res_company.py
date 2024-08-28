# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    documents_vendor_settings = fields.Boolean()
    vendor_folder = fields.Many2one(
        "documents.folder",
        string="Vendors Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_vendor_folder", raise_if_not_found=False
        ),
    )
    vendor_tags = fields.Many2many("documents.tag", "vendor_tags_table")
