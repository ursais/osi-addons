# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edi_vendor_reference = fields.Char(
        string="EDI Vendor Reference",
    )

    edi_partner_document_ids = fields.One2many(
        "edi.partner.doc", "partner_id", string="EDI Partner Documents"
    )
