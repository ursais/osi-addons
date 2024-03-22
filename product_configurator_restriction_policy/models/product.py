# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    restriction_policy = fields.Selection(
        [("standard", "Standard"), ("sequential", "Sequential")],
        string="Restriction Policy",
        default=lambda self: self._get_default_restriction_policy_value(),
        help="""Standard: When the system is calculating the available values from
        restrictions, it will group the restrictions by attribute and then
        determine the values to show.
        Sequential: The the system will go through each restriction individually
        to calculate the available values to show.""",
    )

    def _get_default_restriction_policy_value(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "product_configurator_restriction_policy.restriction_policy",
                default="standard",
            )
        )
