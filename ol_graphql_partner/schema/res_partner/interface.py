# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.interface import BaseInterface
from odoo.addons.ol_graphql.schema.type import CompanyEnumType


class PartnerInterface(BaseInterface):

    city = graphene.String()
    company = graphene.String()
    country_id = graphene.String()
    credit_limit = GenericScalar()
    customer_rank = graphene.Int()
    email = graphene.String()
    # firstname = graphene.String() # TODO: this field does not exist currently
    # has_custom_tc = graphene.Boolean() # TODO: this field does not exist currently
    # has_nda = graphene.Boolean() # TODO: this field does not exist currently
    # hubspot_url = graphene.String() # TODO: this field does not exist currently
    is_company = graphene.Boolean()
    lang = graphene.String()
    # lastname = graphene.String() # TODO: this field does not exist currently
    # late_payment = graphene.Boolean() # TODO: this field does not exist currently
    name = graphene.String()
    # net_terms = graphene.Boolean() # TODO: this field does not exist currently
    # pending_credit = graphene.Float() # TODO: this field does not exist currently
    phone = graphene.String()
    # shared_credit = graphene.Float() # TODO: this field does not exist currently
    state_id = graphene.String()
    street = graphene.String()
    street2 = graphene.String()
    # stripe_customer = graphene.String() # TODO: this field does not exist currently
    supplier_rank = graphene.Int()
    tax_exempt = GenericScalar()
    tax_exemption_code = GenericScalar()
    tax_exemption_number = GenericScalar()
    type = graphene.String()
    vat = graphene.String()
    # vat_vies_validation_state = graphene.String() # TODO: this field does not exist currently
    website = graphene.String()
    zip = graphene.String()
