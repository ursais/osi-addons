# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import UUID
from odoo.addons.ol_graphql.schema.mutator import Mutator
from odoo.addons.ol_graphql_partner.schema.res_partner.types import Partner
from odoo.addons.ol_graphql_partner.schema.res_partner.interface import (
    PartnerInterface,
)
from odoo.addons.ol_graphql_partner.schema.res_partner.decoder import PartnerDecoder


class PartnerInput(graphene.InputObjectType, PartnerInterface):
    """
    Data that can be used to update a partner
    """

    # Fields pointing to ObjectTypes
    account_manager = graphene.InputField(lambda: PartnerInput)
    parent_id = graphene.InputField(lambda: PartnerInput)
    create_id = graphene.InputField(lambda: PartnerInput)
    update_id = graphene.InputField(lambda: PartnerInput)


class PartnerMutator(Mutator, PartnerDecoder):

    def get_fields_to_exclude(self):
        base_fields_to_exclude = super().get_fields_to_exclude()
        partner_fields_to_exclude = [
            # Financial data is owned by the ERP
            "net_terms",
            # ERP should own the ERP URL information
            "odoo_url",
            # Tax and VAT information is managed in the ERP
            "tax_exempt",
            "tax_exemption_code",
            "tax_exemption_number",
            # All `res.partner` records that are synced between the CRM and ERP should have the type `contact` or be Companies
            "type",
        ]

        # Exclude certain fields if the message came from the website
        if self.data.get("message_source", "") == "COMMERCETOOLS":
            partner_fields_to_exclude += [
                "zip",
                "street",
                "street2",
                "city",
                "state_id",
                "country_id",
            ]
        return base_fields_to_exclude + partner_fields_to_exclude

    def process_create_data(self):
        """
        Data processing related to record creation
        """

        # Set the default Customer rank
        self.data["customer_rank"] = 1

        return super().process_create_data()

    def process_update_data(self):
        """
        Data processing related to record update
        """

        # Exclude certain fields if the message came from the website
        if self.data.get("message_source", "") == "COMMERCETOOLS":
            # We don't want to overwrite vat if it's already set on the Odoo record
            if self.odoo_record.vat:
                self.fields_to_exclude += ["vat"]

        return super().process_update_data()


class CreatePartner(graphene.Mutation):
    """
    Create a res.partner object
    """

    class Arguments:
        data = PartnerInput(required=True)

    Output = Partner

    @classmethod
    def mutate(cls, parent, info, data):
        # Create the new mutator instance
        mutator = PartnerMutator(
            info=info,
            odoo_class="res.partner",
            data=data,
            operation="create",
        )
        # Trigger the create process
        return mutator.create()


class UpdatePartner(graphene.Mutation):
    """
    Update a res.partner object
    """

    class Arguments:
        uuid = graphene.Argument(UUID, required=True)
        data = PartnerInput(required=True)

    Output = Partner

    @classmethod
    def mutate(cls, parent, info, uuid, data):
        # Create the new mutator instance
        mutator = PartnerMutator(
            info=info,
            odoo_class="res.partner",
            data=data,
            operation="update",
            uuid=uuid,
        )
        # Trigger the update process
        return mutator.update()


class DeletePartner(graphene.Mutation):
    """
    Delete a res.partner object
    """

    class Arguments:
        uuid = graphene.Argument(UUID, required=True)
        data = PartnerInput(required=True)

    Output = Partner

    @classmethod
    def mutate(cls, parent, info, uuid, data):
        # Create the new mutator instance
        mutator = PartnerMutator(
            info=info,
            odoo_class="res.partner",
            data=data,
            operation="delete",
            uuid=uuid,
        )
        # Trigger the delete process
        return mutator.delete()


class Mutation(graphene.ObjectType):
    """
    Partner Mutation class
    """

    create_partner = CreatePartner.Field()
    update_partner = UpdatePartner.Field()
    delete_partner = DeletePartner.Field()
