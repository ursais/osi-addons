from odoo import api, models, fields


class ProductTemplate(models.Model):
    """
    Adding fields to Product Template.
    """

    _inherit = "product.template"

    # COLUMNS ##########

    triggers_rush = fields.Boolean(
        "Triggers Rush",
        compute="_compute_triggers_rush",
        inverse="_set_rush_order",
        search="_search_rush_order",
    )

    # END ##########
    # METHODS #########

    def _set_rush_order(self):
        self._set_product_variant_field("triggers_rush")

    @api.depends("product_variant_ids.triggers_rush")
    def _compute_triggers_rush(self):
        self._compute_template_field_from_variant_field("triggers_rush")

    def _search_rush_order(self, operator, value):
        subquery = self.with_context(active_test=False)._search(
            [
                ("product_variant_ids.triggers_rush", operator, value),
            ]
        )
        return [("id", "in", subquery)]

    # END ##########
