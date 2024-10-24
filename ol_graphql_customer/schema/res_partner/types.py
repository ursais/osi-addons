# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql_customer.schema.res_partner.interface import (
    CustomerInterface,
)
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType, CompanyEnum


class Customer(OnLogicBaseObjectType, CustomerInterface):
    """
    Graphene type for `res.partner` records
    """

    # Fields pointing to ObjectTypes
    parent_id = graphene.Field(lambda: Customer, required=False)
    create_id = graphene.Field(lambda: Customer)
    update_id = graphene.Field(lambda: Customer)

    @staticmethod
    def resolve_type(partner, _):
        return partner.type.upper() if partner.type else None

    @staticmethod
    def resolve_company(partner, _):
        return partner.company_name or None

    @staticmethod
    def resolve_state_id(partner, _):
        return partner.state_id.code if partner.state_id else None

    @staticmethod
    def resolve_country_id(partner, _):
        return partner.country_id.code if partner.country_id else None

    @staticmethod
    def resolve_parent_id(partner, _):
        return partner.parent_id if partner.parent_id else None

    @staticmethod
    def resolve_create_id(partner, _):
        return partner.sudo().create_uid.partner_id if partner.create_uid else None

    @staticmethod
    def resolve_update_id(partner, _):
        return partner.sudo().write_uid.partner_id if partner.write_uid else None

    @staticmethod
    def resolve_odoo_url(partner, _):
        partner.get_url()

    @staticmethod
    def resolve_tax_exempt(partner, _):
        return Customer.get_company_dependent_field_value(
            base_record=partner, field_name="property_tax_exempt"
        )

    @staticmethod
    def resolve_tax_exemption_code(partner, _):
        """
        Note, depending on which records you are looking at these values can still be null
        even if the associated Sale Order or parent tax exemption fields are set.
        (see set_customer_exemption_data in ls_addons13/ls_account_avatax/models/sale_order.py)
        """
        company_values = Customer.get_company_dependent_field_value(
            base_record=partner,
            field_name=False,
            relations="property_exemption_code_id",
        )
        for company_value in company_values:
            tax_exemption_code_id = company_value["value"]
            if tax_exemption_code_id:
                company_value["value"] = {
                    "name": tax_exemption_code_id.name,
                    "code": tax_exemption_code_id.code,
                }

        return company_values

    @staticmethod
    def resolve_tax_exemption_number(partner, _):
        return Customer.get_company_dependent_field_value(
            base_record=partner, field_name="property_exemption_number"
        )

    @staticmethod
    def resolve_payment_term(partner, _):
        return Customer.get_company_dependent_field_value(
            base_record=partner, field_name="name", relations="property_payment_term_id"
        )

    @staticmethod
    def resolve_credit_limit(partner, _):
        return Customer.get_company_dependent_field_value(
            base_record=partner, field_name="credit_limit"
        )

    @staticmethod
    def resolve_website(partner, _):
        return partner.website or None
