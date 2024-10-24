# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import UUID
from odoo.addons.ol_graphql.schema.mutator import Mutator
from odoo.addons.ol_graphql_customer.schema.res_partner.types import Customer
from odoo.addons.ol_graphql_customer.schema.res_partner.interface import (
    CustomerInterface,
)
from odoo.addons.ol_graphql_customer.schema.res_partner.decoder import CustomerDecoder


class CustomerInput(graphene.InputObjectType, CustomerInterface):
    """
    Data that can be used to update a partner
    """

    # Fields pointing to ObjectTypes
    parent_id = graphene.InputField(lambda: CustomerInput)
    create_id = graphene.InputField(lambda: CustomerInput)
    update_id = graphene.InputField(lambda: CustomerInput)


class CustomerMutator(Mutator, CustomerDecoder):
    pass


class CreateCustomer(graphene.Mutation):
    """
    Create a res.partner object
    """

    class Arguments:
        data = CustomerInput(required=True)

    Output = Customer

    @classmethod
    def mutate(cls, parent, info, data):
        # Create the new mutator instance
        mutator = CustomerMutator(
            info=info,
            odoo_class="res.partner",
            data=data,
            operation="create",
        )
        # Trigger the create process
        return mutator.create()


class UpdateCustomer(graphene.Mutation):
    """
    Update a res.partner object
    """

    class Arguments:
        uuid = graphene.Argument(UUID, required=True)
        data = CustomerInput(required=True)

    Output = Customer

    @classmethod
    def mutate(cls, parent, info, uuid, data):
        # Create the new mutator instance
        mutator = CustomerMutator(
            info=info,
            odoo_class="res.partner",
            data=data,
            operation="update",
            uuid=uuid,
        )
        # Trigger the update process
        return mutator.update()


class DeleteCustomer(graphene.Mutation):
    """
    Delete a res.partner object
    """

    class Arguments:
        uuid = graphene.Argument(UUID, required=True)
        data = CustomerInput(required=True)

    Output = Customer

    @classmethod
    def mutate(cls, parent, info, uuid, data):
        # Create the new mutator instance
        mutator = CustomerMutator(
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
    Customer Mutation class
    """

    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()
