# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    documents_partner_settings = fields.Boolean()
    partner_folder = fields.Many2one(
        "documents.folder",
        string="Partner Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_partner_folder", raise_if_not_found=False
        ),
    )
    partner_tags = fields.Many2many("documents.tag", "partner_tags_table")
