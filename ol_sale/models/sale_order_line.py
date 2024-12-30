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

    def update_crm_tag_sale_order(self):
        tag_engineering_prototype = self.env.ref("ol_sale.crm_tag_engineering_prototype")
        tag_ids = self.order_id.tag_ids.ids
        if self.order_id and self.product_template_id.product_state_id.id == self.env.ref("ol_sale.product_state_prototype").id:
            if self._context.get("from_unlink"):
                tag_ids.remove(tag_engineering_prototype.id)
                self.order_id.tag_ids = [(6,0,tag_ids)]
            else:
                self.order_id.tag_ids = [(6,0,tag_engineering_prototype.ids)]
        elif self.product_template_id.product_state_id.id != tag_engineering_prototype.id and tag_engineering_prototype.id in self.order_id.tag_ids.ids:
            tag_ids.remove(tag_engineering_prototype.id)
            self.order_id.tag_ids = [(6,0,tag_ids)]

    @api.model_create_multi
    def create(self, vals):
        """
        Override create method to include attribute values in the name
        of the record based on product attribute line settings.
        """
        res = super().create(vals)

        for rec in res:
            rec.name = get_product_description(rec.product_id)
            rec.update_crm_tag_sale_order()
            product_bom = self.env['mrp.bom'].search(['|', ('product_id', '=', rec.product_id.id), ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)], limit=1)
            if product_bom and not rec.bom_id and not rec.bom_id.scaffolding_bom:
                rec.bom_id = product_bom.id
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
            rec.update_crm_tag_sale_order()
            product_bom = self.env['mrp.bom'].search(['|', ('product_id', '=', rec.product_id.id), ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)], limit=1)
            if product_bom and not rec.bom_id and not rec.bom_id.scaffolding_bom:
                rec.bom_id = product_bom.id
            if not product_bom and rec.bom_id:
                rec.bom_id = False
        return res

    def unlink(self):
        self.with_context(from_unlink=True).update_crm_tag_sale_order()
        return super().unlink()

    # END #########
