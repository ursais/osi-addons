from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    group_rma_delivery_address = fields.Boolean(
        string="RMA addresses",
        help="Display 3 fields on rma: partner, invoice address, delivery address",
    )

    group_rma_lines = fields.Boolean(
        string="Use RMA groups", help="Group RMA lines in one RMA group"
    )
