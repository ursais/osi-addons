# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class SaleOrderRecurrence(models.Model):
    _inherit = "sale.temporal.recurrence"

    factor = fields.Float(default=1.0)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    populate_recurrence_price_ids = fields.Many2many(
        "product.pricing", string="Populate Recurrence Price"
    )
