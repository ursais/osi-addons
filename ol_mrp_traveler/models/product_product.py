# Import Odoo libs
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    Traveler related fields and functionality
    """

    _inherit = "product.product"

    # COLUMNS #####

    check_ids = fields.Many2many(
        comodel_name="mrp.assembly.check",
        string="Assembly Checks",
        compute="_compute_check_ids",
    )
    bios_name = fields.Char(
        string="BIOS Name",
        compute="_compute_bios_name",
    )

    variant_check_ids = fields.Many2many(
        comodel_name="mrp.assembly.check",
        string="Variant Assembly Checks",
    )
    variant_bios_name = fields.Char(string="Variant BIOS Name")

    # END #########

    @api.depends(
        "variant_bios_name",
        "template_bios_name",
    )
    def _compute_bios_name(self):
        """
        Compute from variant and template settings
        """
        for product in self:
            # take the product bios name if there is one, otherwise take the template one
            product.bios_name = (
                product.variant_bios_name
                if product.variant_bios_name
                else product.template_bios_name
            )

    @api.depends(
        "template_check_ids",
        "variant_check_ids",
    )
    def _compute_check_ids(self):
        """
        Compute overall checks (both variant and template)
        """
        for product in self:
            product.check_ids = product.template_check_ids | product.variant_check_ids
