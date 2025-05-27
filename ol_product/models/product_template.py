# Import Odoo Libs
from odoo import fields, models

SYSTEM_TIERS = [
    ("normal", "Normal System"),
    ("custom_created", "Custom Created System"),
    ("customer", "Customer System"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    """
    Add length,width and height to ProductTemplate
    """

    # METHODS #####

    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")

    system_tier = fields.Selection(
        selection=SYSTEM_TIERS,
        string="System Tier",
        default=None,
    )

    def is_stockable(self):
        """
        Check if this product should have stock values or not
        """

        if self.has_configurable_attributes or self.type != "product":
            # Product should not have stock values
            # a.k.a Systems, Services, Virtual, Consumable
            return False

        return True

    # END #########
