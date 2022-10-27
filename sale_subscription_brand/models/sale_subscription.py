# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    brand_id = fields.Many2one("res.brand", string="Brand")

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.brand_id:
            res.update({"brand_id": self.brand_id.id})
        return res
