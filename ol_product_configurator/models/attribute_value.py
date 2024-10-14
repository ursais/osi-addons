# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeValue(models.Model):
    _inherit = "product.attribute.value"
    """
    Inherit the Product Attribute Value Object Adding Fields and methods
    """

    company_id = fields.Many2one("res.company", string="Company")

    # METHODS ##########

    @api.constrains("product_id", "company_id")
    def _check_company_ids(self):
        product_company = self.product_id.company_id
        if (
            self.product_id
            and product_company
            and product_company.id != self.company_id.id
        ):
            raise ValidationError(
                _(
                    "The company '%s' cannot be added because the product '%s' is assigned to the company '%s'."
                    % (self.company_id.name, self.product_id.name, product_company.name)
                )
            )

    # END ##########
