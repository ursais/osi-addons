# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ProductTemplate(models.Model):

    _inherit = ["product.template", "attribute.set.owner.mixin"]
    _name = "product.template"

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        default=lambda self: self._get_default_att_set(),
    )

    def _get_default_att_set(self):
        """Get default product's attribute_set by category."""
        default_categ_id_id = self._get_default_category_id()
        if default_categ_id_id:
            default_categ_id = self.env["product.category"].search(
                [("id", "=", default_categ_id_id.id)], limit=1
            )
            return default_categ_id.attribute_set_id.id

    @api.model_create_multi
    def create(self, vals_list):
        category_model = self.env["product.category"]
        for vals in vals_list:
            if not vals.get("attribute_set_id") and vals.get("categ_id"):
                category = category_model.browse(vals["categ_id"])
                vals["attribute_set_id"] = category.attribute_set_id.id
        return super().create(vals_list)

    def write(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            vals["attribute_set_id"] = category.attribute_set_id.id
        return super().write(vals)

    @api.onchange("categ_id")
    def _onchange_categ_id(self):
        self.ensure_one()
        if self.categ_id and not self.attribute_set_id:
            self.attribute_set_id = self.categ_id.attribute_set_id


class ProductProduct(models.Model):

    _inherit = ["product.product", "attribute.set.owner.mixin"]
    _name = "product.product"

    attribute_set_id = fields.Many2one(
        related="product_tmpl_id.attribute_set_id", store=True
    )

    @api.model
    def _get_attribute_set_owner_model(self):
        return [("model", "in", ("product.product", "product.template"))]
