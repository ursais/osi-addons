# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import Command, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    populate_recurrence_price_ids = fields.Many2many(
        "sale.temporal.recurrence", string="Populate Recurrence Price", copy=False
    )
    product_pricing_ids = fields.One2many(
        compute="_compute_time_based_pricing_product_attributes",
        store=True,
        readonly=False,
    )

    @api.depends("populate_recurrence_price_ids")
    def _compute_time_based_pricing_product_attributes(self):
        for template in self:
            populate_recurrence_price = (
                template.populate_recurrence_price_ids
                and template.populate_recurrence_price_ids[0]
                or False
            )
            if populate_recurrence_price:
                populate_recurrence_price = (
                    populate_recurrence_price._origin
                    if isinstance(populate_recurrence_price.id, models.NewId)
                    else populate_recurrence_price or False
                )
                template.product_pricing_ids.unlink()
                product_pricing_list = []
                for variant in template.product_variant_ids:
                    price = template.list_price
                    vals = {
                        "product_template_id": template.id or template._origin.id,
                        "product_variant_ids": [
                            (6, 0, [variant.id or variant._origin.id])
                        ],
                        "recurrence_id": populate_recurrence_price.id,
                        "price": price * populate_recurrence_price.factor,
                        "pricelist_id": self.env.ref("product.list0").id,
                    }
                    product_pricing_list.append(Command.create(vals))
                template.product_pricing_ids = product_pricing_list
            else:
                template.product_pricing_ids.unlink()
