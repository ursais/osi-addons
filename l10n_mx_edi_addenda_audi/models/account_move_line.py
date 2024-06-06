from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    audi_line_product_ref = fields.Char(
        string="Product Reference", compute="_compute_audi_line_product_ref"
    )

    @api.onchange("product_id")
    def _compute_audi_line_product_ref(self):
        for record in self:
            record.audi_line_product_ref = record.product_id.audi_product_ref
