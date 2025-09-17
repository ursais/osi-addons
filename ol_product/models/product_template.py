# Import Odoo Libs
from odoo import fields, models

SYSTEM_TIERS = [
    ("normal", "Normal System (Portfolio)"),
    ("custom_created", "Custom Created System (Tier 1)"),
    ("customer", "Customer System  (Tier 2)"),
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

    # TODO: Un-comment and update the code below if we have final decisions and information on the phantom kit logic
    # is_kits = fields.Boolean(
    #     string="Is Phantom Kit",
    #     help=(
    #         "Helper field to know if a product is a Phantom Kit. "
    #         "We only consider a product a Phantom Kit if it has a valid Kit BOM"
    #     ),
    #     compute="_compute_is_kits",
    #     store=True,
    #     readonly=True,
    # )

    # @api.depends("bom_ids", "bom_ids.type")
    # def _compute_is_kits(self):
    #     """
    #     Helper function to compute if a product is a phantom kit based on its BOMs.
    #     TODO: This method is not precise, it just checks if any phantom BOMs for the product exists.
    #           This means any user errors (mixing phantom and normal boms) is not checked and validated
    #     """
    #     # Pre-fetch relevant BOMs for efficiency if dealing with many products
    #     products_with_boms = self.filtered("bom_ids")
    #     if not products_with_boms:
    #         # Set False for products without any BOMs
    #         for product in self:
    #             product.is_kits = False
    #         # Exit early
    #         return

    #     # Fetch relevant BoM types for the products that have BoMs
    #     # This avoids iterating BoMs one by one inside the loop for better performance
    #     bom_data = self.env["mrp.bom"].search_read(
    #         [("product_tmpl_id", "in", products_with_boms.ids), ("type", "=", "phantom")], ["product_tmpl_id"]
    #     )
    #     # Create a set of template IDs that have at least one phantom BoM
    #     phantom_tmpl_ids = {bom["product_tmpl_id"][0] for bom in bom_data}

    #     for product in self:
    #         # Check if the product's ID is in the set of templates with phantom BoMs
    #         product.is_kits = product.id in phantom_tmpl_ids

    def get_phantom_kit_components(self):
        """
        Get the components of the Phantom Kit
        """

        if not self.is_phantom_kit:
            # Non Phantom Kits will have no components
            return False

        # Get the Phantom Bom
        phantom_bom = self.get_phantom_bom()

        if not phantom_bom:
            # If no Phantom BOM is defined return an empty recordset
            return self.env["product.product"]

        # Return the product.product records associated with the Phantom Bom's bom lines
        return phantom_bom.mapped("bom_line_ids.product_id")

    def get_phantom_bom(self):
        """
        Get the latest Phantom Bom of a products
        TODO: Discuss with the Business/OSI what the logic is to find the latest active BOM
        """
        phantom_bom = self.bom_ids.filtered(lambda b: b.type == "phantom").sorted(
            key="version", reverse=True
        )
        return phantom_bom[0] if phantom_bom else self.env["mrp.bom"]
