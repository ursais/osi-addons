# Import Odoo libs
from odoo import _, api, fields, models, exceptions


class MRPBom(models.Model):
    """
    Inherit BoM, adding scaffolding BoM field and methods.
    """

    _inherit = "mrp.bom"

    # COLUMNS #####

    scaffolding_bom = fields.Boolean(string="Scaffolding BoM")

    # END #########
    # METHODS #####

    @api.constrains("product_tmpl_id")
    def _check_product_tmpl_scaffolding_bom(self):
        """Constraint ensures only one scaffolding BoM exists per product template"""
        for rec in self:
            if (
                self.search_count(
                    [
                        ("scaffolding_bom", "=", True),
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                    ]
                )
                > 1
            ):
                raise exceptions.ValidationError(
                    _(
                        "Only one Scaffolding BoM can exist for the Product [%s]"
                        % rec.product_tmpl_id.name
                    )
                )

    @api.onchange("product_id")
    def onchange_scaffolding_bom_product_id(self):
        """onchange method to automatically set 'scaffolding_bom'
        based on 'product_id'."""
        if self.product_id:
            self.scaffolding_bom = False
        else:
            self.scaffolding_bom = True

    # END #########
