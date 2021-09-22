# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiCompanyDoc(models.Model):
    _name = "edi.company.doc"
    _description = "EDI Company Document"

    company_id = fields.Many2one("res.company", string="Company")
    edi_supported_doc_id = fields.Many2one(
        "edi.supported.doc", string="EDI Supported Document"
    )
