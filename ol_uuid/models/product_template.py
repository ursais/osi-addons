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
        require=True,
        copy=False,
        index=True,
    )
    # END #########

    @api.model_create_multi
    def create(self, values):
        """
        Make sure system variant's have their own unique UUID.
        """

        if not values.get("variant_uuid", False):
            uuid = self.env[self._name].get_uuid(force_new=True)
            values["variant_uuid"] = uuid
        res = super().create(values)
        return res
