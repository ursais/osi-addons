# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiProductConfig(models.Model):
    _name = "edi.product.config"
    _description = "Edi Product Config"

    product_id = fields.Many2one("product.product", string="Product")
    edi_supported_doc_id = fields.Many2one(
        "edi.supported.doc", string="EDI Supported Document"
    )
