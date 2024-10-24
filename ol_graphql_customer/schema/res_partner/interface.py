# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.interface import BaseInterface


class CustomerInterface(BaseInterface):

    name = graphene.String()
    email = graphene.String()
    type = graphene.String()
    phone = graphene.String()
    is_company = graphene.Boolean()
    company = graphene.String()
    city = graphene.String()
    country_id = graphene.String()
    state_id = graphene.String()
    street = graphene.String()
    street2 = graphene.String()
    zip = graphene.String()
    tax_exempt = GenericScalar()
    tax_exemption_code = GenericScalar()
    tax_exemption_number = GenericScalar()
    payment_term = GenericScalar()
    credit_limit = GenericScalar()
    website = graphene.String()
    vat = graphene.String()
    lang = graphene.String()
    supplier_rank = graphene.Int()
    customer_rank = graphene.Int()
