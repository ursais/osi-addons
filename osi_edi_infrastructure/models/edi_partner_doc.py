# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiPartnerDoc(models.Model):
    _name = "edi.partner.doc"
    _description = "EDI Partner Document"

    partner_id = fields.Many2one("res.partner", string="Partner")
    edi_supported_doc_id = fields.Many2one(
        "edi.supported.doc", string="EDI Supported Document"
    )
    code = fields.Selection(
        related="edi_supported_doc_id.code", string="Code", store=True
    )
