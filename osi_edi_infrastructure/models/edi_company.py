# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    edi_comp_doc_ids = fields.One2many(
        "edi.company.doc", "company_id", string="EDI Active Documents"
    )
    edi_provider_id = fields.Many2one("edi.provider", string="EDI Provider")
