# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends_context("company")
    @api.depends("last_purchase_line_ids.state")
    def _compute_last_purchase_line_id(self):
        """Override method in purchase_last_price_info module to make sure
        purchase orders for internal companies don't count towards last purchase."""
        company_partners = (
            self.env["res.company"].sudo().search([]).mapped("partner_id")
        )
        for item in self:
            item.last_purchase_line_id = fields.first(
                item.last_purchase_line_ids.sudo().filtered_domain(
                    [
                        ("state", "in", ["purchase", "done"]),
                        ("company_id", "in", self.env.companies.ids),
                        ("partner_id", "not in", company_partners.ids),
                    ]
                )
            )
