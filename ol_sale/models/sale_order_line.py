# Import Odoo libs
from odoo import api, fields, models
from odoo.addons.ol_base.tools import get_product_description


class SaleOrderLine(models.Model):
    """
    Add new fields to Sale Order Line
    """

    _inherit = "sale.order.line"

    # COLUMNS #####

    product_state_id = fields.Many2one(related="product_template_id.product_state_id")

    # END #########
    # METHODS #####

    @api.model_create_multi
    def create(self, vals):
        """
        Override create method to include attribute values in the name
        of the record based on product attribute line settings.
        """
        res = super().create(vals)

        for rec in res:
            rec.name = get_product_description(rec.product_id)

        return res

    def write(self, vals):
        """
        Override write method to update record's name with attribute values
        based on changes in 'product_id' and attribute line settings.
        """
        res = super().write(vals)

        for rec in self:
            # If 'product_id' is being updated, adjust the record's description
            if vals.get("product_id"):
                product = rec.env["product.product"].browse(vals["product_id"])
                rec.name = get_product_description(product)

        return res

    # END #########
