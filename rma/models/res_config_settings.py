# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_rma_delivery_address = fields.Boolean(
        related="company_id.group_rma_delivery_address",
        implied_group="rma.group_rma_delivery_invoice_address",
        readonly=False,
    )

    group_rma_lines = fields.Boolean(
        related="company_id.group_rma_lines",
        readonly=False,
        implied_group="rma.group_rma_groups",
    )

    module_rma_account = fields.Boolean(string="RMA invoicing")
