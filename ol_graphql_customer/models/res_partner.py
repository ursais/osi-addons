# Import Odoo libs
from odoo import models


class ResPartner(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "res.partner"
    _inherit = ["res.partner", "graphql.mixin"]

    def get_graphql_placeholder_values(
        self, message_field=False, message_values=False, transaction_id=False
    ):
        base_values = super().get_graphql_placeholder_values(
            message_field=message_field,
            message_values=message_values,
            transaction_id=transaction_id,
        )
        partner_base_values = {
            # Customers are global (i.e. are not associated with a specific company) so we explicitly set company_id to false
            "default": {"company_id": False, "customer_rank": 1},
            # Customers can only have companies as their parents
            "parent_id": {"is_company": True},
        }
        # Get the base values, and if we have additional values for the specific message_values,
        # update the base values with those
        partner_values = partner_base_values.get("default", {})
        if message_field:
            partner_values.update(partner_base_values.get(message_field, {}))

        # Merge the super and customer specific values
        base_values.update(partner_values)

        return base_values
