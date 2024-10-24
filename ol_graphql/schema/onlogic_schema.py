"""
Auto load the GraphQL Schema from the given folder structure.
Base idea from: https://github.com/graphql-python/graphene/issues/545#issuecomment-329630141
"""

# Import Python Libs
import os
import graphene
import logging
import importlib
from pathlib import Path
from inspect import getmembers, isclass

# Import Odoo Libs
from odoo import modules, fields
from odoo.addons.graphql_base import types


_logger = logging.getLogger(__name__)

# ==================================================================
# Monkey patch OCA module's `odoo_attr_resolver` method
# ==================================================================
OLD_RESOLVER = types.odoo_attr_resolver


def new_odoo_attr_resolver(attname, default_value, root, info, **args):
    """An attr resolver that is specialized for Odoo recordsets.

    It converts False to None, except for Odoo Boolean fields.
    This is necessary because Odoo null values are often represented
    as False, and graphene would convert a String field with value False
    to "false".

    @ol_upgrade: It `DOES NOT` converts datetimes to the user timezone.

    It also raises an error if the attribute is not present, ignoring
    any default value, so as to return if the schema declares a field
    that is not present in the underlying Odoo model.
    """
    value = getattr(root, attname)
    field = root._fields.get(attname)
    if value is False:
        if not isinstance(field, fields.Boolean):
            return None
    # @ol_upgrade(-2/0) We don't want to convert the UTC datetime values to the users local timezone
    # elif isinstance(field, fields.Datetime):
    # return fields.Datetime.context_timestamp(root, value)
    return value


types.odoo_attr_resolver = new_odoo_attr_resolver


class QueriesAbstract(graphene.ObjectType):
    pass


class MutationsAbstract(graphene.ObjectType):
    pass


class GQLLoader:
    def __init__(self):
        # TODO: module layout different from odoo 13, do we want to change this here or in docker structure?
        # A ticket exists for this work here: https://logicsupply.atlassian.net/browse/DEV-19549
        os.chdir("../")
        self.onlogic_modules = f"/mnt/extra-addons/private-addons/onlogic-addons"
        self.directories_to_exclude = ["__pycache__", "_base"]
        self.modules = self.get_modules()
        # Set up the base data
        self.graphql_data = {
            "queries": {
                "classes": [QueriesAbstract],
                "class_filter": "Query",
                "properties": {},
            },
            "mutations": {
                "classes": [MutationsAbstract],
                "class_filter": "Mutation",
                "properties": {},
            },
        }
        self.set_graphql_data()

    def get_modules(self):
        """
        Get all modules that are Graphql aware
        """
        gql_modules = []
        for mod_name in modules.get_modules():
            manifest_values = self.get_module_info(mod_name)
            if manifest_values.get("graphql", False):
                gql_modules.append(mod_name)
        return gql_modules

    @classmethod
    def get_module_info(cls, name):
        try:
            return modules.get_manifest(name)
        except Exception as e:
            _logger.exception(e)
            return {}

    def set_graphql_data(self):
        # Define the base data collector dictionary

        for module_name in self.modules:
            os_path = f"{self.onlogic_modules}/{module_name}/schema"
            module_path = f"odoo.addons.{module_name}.schema"

            # Get all of the subdirectories in here.
            # ex. `product`, `sale_order` etc.
            subdirectories = [
                x
                for x in os.listdir(os_path)
                if os.path.isdir(os.path.join(os_path, x))
                and x not in self.directories_to_exclude
            ]

            # For each GraphQL operation type ('queries', 'mutations') collect all the related Classes
            for operation_type in ["queries", "mutations"]:
                # Set the variables in which we want to store the collected data
                classes = self.graphql_data[operation_type]["classes"]
                class_filter = self.graphql_data[operation_type]["class_filter"]
                properties = self.graphql_data[operation_type]["properties"]

                # Loop through each folder in here, ex. `product`, `sale_order`
                for directory in subdirectories:

                    if not os.path.isfile(f"{os_path}/{directory}/{operation_type}.py"):
                        # If not queries/mutations are defined we can skip this folder
                        continue

                    try:
                        # As we don't have `__init__` files in these subdirectories we need to manually initialize them
                        module = importlib.import_module(
                            f"{module_path }.{directory}.{operation_type}"
                        )
                        if module:
                            # If we correctly initialize the module ex. `product` find all class definition in that module ex. queries.py
                            module_classes = [x for x in getmembers(module, isclass)]
                            # Filter down to the classes that match the currect operation_type, ex. `Query` or `Mutation`
                            # This is why it's important to use these class names in those files!
                            classes += [
                                x[1] for x in module_classes if class_filter == x[0]
                            ]
                    except ModuleNotFoundError:
                        _logger.exception(
                            f"GraphQL: Could not load Model `{directory}`"
                        )

                # Reverse the order of the classes
                classes = classes[::-1]
                for base_class in classes:
                    # Gather the properties needed for the Schema class definition based on the fields
                    properties.update(base_class.__dict__["_meta"].fields)


# Initialize the GraphQL Loader
graphql_data = GQLLoader().graphql_data

# Set the results that we can use in the module_schema.py file
Queries = type(
    "Queries",
    tuple(graphql_data["queries"]["classes"]),
    graphql_data["queries"]["properties"],
)
Mutations = type(
    "Mutations",
    tuple(graphql_data["mutations"]["classes"]),
    graphql_data["mutations"]["properties"],
)

# Create the final GraphQL Schema based on the Queries and Mutations assambled in the loader.py file
schema = graphene.Schema(query=Queries, mutation=Mutations, auto_camelcase=False)
