# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _domain_company(self):
        company = self.env.company
        return ["|", ("company_id", "=", False), ("company_id", "=", company)]

    documents_helpdesk_settings = fields.Boolean()
    helpdesk_folder = fields.Many2one(
        "documents.folder",
        string="Helpdesk Workspace",
        domain=_domain_company,
        default=lambda self: self.env.ref(
            "documents_helpdesk.documents_folder_helpdesk",
            raise_if_not_found=False,
        ),
    )
    document_helpdesk_tags = fields.Many2many(
        "documents.tag", "document_helpdesk_tag", string="Helpdesk Tags"
    )
