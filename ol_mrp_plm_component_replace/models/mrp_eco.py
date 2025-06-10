# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MRPEco(models.Model):
    """
    Inherit MRP Eco for adding replace component functionality.
    """

    _inherit = "mrp.eco"

    # COLUMNS #####

    product_to_add_id = fields.Many2one(
        comodel_name="product.product",
        string="New Component",
    )
    bom_ids = fields.Many2many(
        comodel_name="mrp.bom",
        relation="mrp_eco_bom_rel",
        column1="eco_id",
        column2="bom_id",
        string="Affected BoMs",
        help=(
            "BoMs that use the product to remove. "
            "You can manually remove any BoMs from the list to skip them."
        ),
    )

    # END #########
    # METHODS ##########

    @api.onchange("product_tmpl_id", "type_id")
    def _onchange_product_id_bom_ids(self):
        for eco in self:
            if (
                eco.type_id.component_replacement
                and eco.product_tmpl_id.product_variant_id
            ):
                bom_lines = self.env["mrp.bom.line"].search(
                    [("product_id", "=", eco.product_tmpl_id.product_variant_id.id)]
                )
                eco.bom_ids = bom_lines.filtered(
                    lambda l: l.bom_id.scaffolding_bom
                ).mapped("bom_id")
            else:
                eco.bom_ids = False

    def action_apply(self):
        for eco in self:
            if eco.type_id.component_replacement:
                if not eco.product_tmpl_id or not eco.product_to_add_id:
                    raise ValidationError(
                        _(
                            "Both 'Component to Remove' and 'Component to Add' must be set."
                        )
                    )
                for bom in eco.bom_ids:
                    # Find attribute line(s) that reference the old product
                    attr_lines = self.env["product.template.attribute.line"].search(
                        [
                            ("product_tmpl_id", "=", bom.product_tmpl_id.id),
                            (
                                "value_ids.product_id",
                                "=",
                                eco.product_tmpl_id.product_variant_id.id,
                            ),
                        ]
                    )

                    for line in attr_lines:
                        value_to_remove = line.value_ids.filtered(
                            lambda v: v.product_id
                            == eco.product_tmpl_id.product_variant_id
                        )
                        value_to_add = self.env["product.attribute.value"].search(
                            [
                                ("attribute_id", "=", line.attribute_id.id),
                                (
                                    "product_id",
                                    "=",
                                    eco.product_to_add_id.product_variant_id.id,
                                ),
                            ]
                        )

                        if not value_to_add:
                            raise ValidationError(
                                _(
                                    """Cannot replace component: '%s' is missing a matching
                                      attribute value on the new product."""
                                )
                                % eco.product_to_add_id.display_name
                            )

                        line.write(
                            {
                                "value_ids": [
                                    (3, value_to_remove.id),
                                    (4, value_to_add.id),
                                ],
                                "default_val": (
                                    value_to_add.id
                                    if line.default_val.id == value_to_remove.id
                                    else line.default_val.id
                                ),
                            }
                        )

                    # Archive the old BoMs and rebuild with new attribute values
                    bom.product_tmpl_id.action_create_rebuild_scaffolding_bom()
            else:
                return super().action_apply()

    # END #########
