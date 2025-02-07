# Import Odoo Libs
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    Updates to product variants to support configurations
    """

    _inherit = "product.product"

    # COLUMNS #####

    classification_ids = fields.Many2many(
        comodel_name="product.attribute.classification",
        string="BoM Line Options",
        compute="_compute_classifications",
        store=True,
    )
    bom_line_ids = fields.One2many(
        comodel_name="mrp.bom.line",
        inverse_name="product_id",
        string="BoM Lines",
    )

    # END #########
    # METHODS #####

    @api.depends("bom_line_ids.classification_id")
    def _compute_classifications(self):
        """Compute classifications efficiently using dependencies"""
        for product in self:
            product.classification_ids = product.bom_line_ids.mapped(
                "classification_id"
            )

    # END #########
