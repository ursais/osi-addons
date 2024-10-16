# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeValue(models.Model):
    _inherit = "product.attribute.value"
    """
    Inherit the Product Attribute Value Object Adding Fields and methods
    """

    # COLUMNS ##########

    company_ids = fields.Many2many("res.company", string="Companies")

    # END ##########
    # METHODS ##########

    @api.constrains("product_id", "company_ids")
    def _check_company_ids(self):
        product_company = self.product_id.company_id
        if self.product_id and product_company and self.company_ids:
            for company in self.company_ids:
                if product_company.id != company.id:
                    raise ValidationError(
                        _(
                            "The company '%s' cannot be added because the product '%s' is assigned to the company '%s'."
                            % (company.name, self.product_id.name, product_company.name)
                        )
                    )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        # Call super to get the original name_search result
        res = super().name_search(name=name, args=args, operator=operator, limit=limit)

        # Only apply the filtering if we're in the wizard context
        if self.env.context.get("wizard_id"):
            # Get the logged-in user's company
            user_company_id = self.env.company.id

            # Filter the results based on company criteria
            filtered_res = [
                result
                for result in res
                if not self.browse(result[0]).company_ids
                or user_company_id in self.browse(result[0]).company_ids.ids
            ]

            return filtered_res

        return res

    @api.model
    def web_search_read(
        self, domain, specification, offset=0, limit=None, order=None, count_limit=None
    ):
        # Call the super method first to get the initial results
        res = super().web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

        # Only apply the filtering if we're in the wizard context
        if self.env.context.get("wizard_id"):
            # Get the logged-in user's company
            user_company_id = self.env.company.id

            # Only apply the filtering if there are results to filter
            if res and res.get("records"):
                filtered_records = []

                # Filter records based on the 'company_ids' field
                for record in res["records"]:
                    value = self.browse(record["id"])
                    if (
                        not value.company_ids
                        or user_company_id in value.company_ids.ids
                    ):
                        filtered_records.append(record)

                # Update the results with the filtered records
                res["records"] = filtered_records

        return res

    # END ##########
