# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rma_customer_operation_id = fields.Many2one(
        company_dependent=True,
        comodel_name="rma.operation",
        string="Default RMA Customer Operation",
    )
    rma_supplier_operation_id = fields.Many2one(
        company_dependent=True,
        comodel_name="rma.operation",
        string="Default RMA Supplier Operation",
    )
    rma_approval_policy = fields.Selection(
        related="categ_id.rma_approval_policy", readonly=True
    )
