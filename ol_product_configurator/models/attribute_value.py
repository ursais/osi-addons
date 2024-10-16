# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeValue(models.Model):
    _inherit = "product.attribute.value"
    """
    Inherit the Product Attribute Value Object Adding Fields and methods
    """

    company_ids = fields.Many2many("res.company", string="Company")

    # METHODS ##########

    @api.constrains("product_id", "company_ids")
    def _check_company_ids(self):
        product_company = self.product_id.company_id
        if self.product_id and product_company and self.company_ids:
            for company in self.company_ids:
                if product_company.id != company.id:
                    raise ValidationError(_(
                    "The company '%s' cannot be added because the product '%s' is assigned to the company '%s'."
                    % (company.name, self.product_id.name, product_company.name)))

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if not domain:
            doamin = []
        company = self.env.company.ids
        if self._context.get("default_attribute_id"):
            domain.extend(['|', ('company_ids', 'in', company), ('company_ids', '=', False)])
        return super()._name_search(name, domain, operator, limit, order)
    # END ##########
