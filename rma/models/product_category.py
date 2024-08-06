# Copyright 2017 ForgeFlow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    rma_approval_policy = fields.Selection(
        selection=[("one_step", "One step"), ("two_step", "Two steps")],
        string="RMA Approval Policy",
        required=True,
        default="one_step",
        help="Options: \n "
        "* One step: Always auto-approve RMAs that only contain "
        "products within categories with this policy.\n"
        "* Two steps: A RMA containing a product within a category with "
        "this policy will request the RMA manager approval.",
    )
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
