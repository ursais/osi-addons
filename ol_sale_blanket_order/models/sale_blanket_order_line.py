# Import Odoo libs
from odoo import api, fields, models


class SaleBlanketOrderLine(models.Model):
    """
    Add new fields to Sale blanket Order Line
    """

    _inherit = "sale.blanket.order.line"

    # COLUMNS #####

    customer_lead = fields.Float(
        compute="_compute_customer_lead",
        store=True,
        readonly=False,
        precompute=True,
    )
    product_state_id = fields.Many2one(
        "product.state",
        related="product_id.product_state_id",
    )

    # END #########

    # METHODS #########

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            if rec.product_id.product_template_attribute_value_ids:
                description = rec.product_id.name
                for (
                    attribute_value
                ) in rec.product_id.product_template_attribute_value_ids:
                    # Get the product.template.attribute.line for this attribute_value
                    attribute_line = (
                        rec.product_id.product_tmpl_id.attribute_line_ids.filtered(
                            lambda line: line.attribute_id
                            == attribute_value.attribute_id
                        )
                    )
                    # Check if used_in_sale_description is True on the product.template.attribute.line
                    if attribute_line and attribute_line.used_in_sale_description:
                        description += "\n  " + attribute_value.display_name
                rec.name = description
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if vals.get("product_id"):
                product = rec.env["product.product"].browse(vals["product_id"])
                if product.product_template_attribute_value_ids:
                    description = product.name
                    for attribute_value in product.product_template_attribute_value_ids:
                        # Get the product.template.attribute.line for this attribute_value
                        attribute_line = (
                            product.product_tmpl_id.attribute_line_ids.filtered(
                                lambda line: line.attribute_id
                                == attribute_value.attribute_id
                            )
                        )
                        # Check if used_in_sale_description is True on the product.template.attribute.line
                        if attribute_line and attribute_line.used_in_sale_description:
                            description += "\n  " + attribute_value.display_name
                    rec.name = description
        return res

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay

    # END ######
