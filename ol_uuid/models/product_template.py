# Import Odoo libs
from odoo import models, api
from odoo.addons.ol_base.fields import fields as ol_fields


class ProductTemplate(models.Model):
    """
    Add UUID compatibility
    """

    _name = "product.template"
    _inherit = ["product.template", "res.uuid"]


class ProductProduct(models.Model):
    """
    Add variant UUID compatibility
    """

    _inherit = "product.product"

    # COLUMNS #####
    variant_uuid = ol_fields.Uuid(
        string="Variant UUID",
        help="Unique identifier that is used to identify this product variant between different systems.",
        required=True,
        copy=False,
        index=True,
    )
    # END #########

    @api.model_create_multi
    def create(self, vals_list):
        """
        Make sure system variant's have their own unique UUID.
        """
        for vals in vals_list:
            if not vals.get("variant_uuid", False):
                uuid = self.env[self._name].get_uuid(force_new=True)
                vals["variant_uuid"] = uuid
        return super().create(vals_list)
