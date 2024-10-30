# Import Python Libs
import graphene
from collections import defaultdict

# Import Odoo libs
from graphene.types.generic import GenericScalar
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType
from odoo.addons.ol_graphql_product.schema.product.interface import (
    ProductTemplateInterface,
)
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType, CompanyEnum
from odoo.addons.ol_graphql_product.schema.product_pricelist_item.types import (
    ProductPricelistItem,
)
from odoo.addons.ol_graphql_product.schema.product_configuration_relation.types import (
    ProductConfigurationRelation,
)
from odoo.addons.ol_graphql_product.schema.product_configuration_option.types import (
    ProductConfigurationOption,
)


class ProductTypeEnum(graphene.Enum):
    """
    Enumeration of valid product types
    These map to product.category records attached to products
    """

    SERVICE = "service"
    SYSTEM = "system"
    COMPONENT = "component"


class ProductTemplate(OnLogicBaseObjectType, ProductTemplateInterface):
    """
    Graphene type for `product.template` records
    """

    description = graphene.String()
    active = GenericScalar()
    base_price = GenericScalar()
    lifecycle_status = GenericScalar()
    product_tax_code = GenericScalar()
    lifecycle_launch_date = graphene.Date()
    public_destination = graphene.String()
    sku = graphene.String(required=True)
    type = graphene.Field(ProductTypeEnum)
    message_origin = graphene.String()
    # options = graphene.List(ProductConfigurationRelation)
    special_price = GenericScalar()
    image = GenericScalar()

    @staticmethod
    def resolve_image(product, _):
        return product.image_1920

    @staticmethod
    def resolve_message_origin(product, _):
        return "ODOO"

    @staticmethod
    def resolve_type(product, info):
        env = info.context["env"]
        mapping = {
            env.ref("ol_base.product_category_systems"): ProductTypeEnum.SYSTEM,
            env.ref("ol_base.product_category_services"): ProductTypeEnum.SERVICE,
            env.ref("ol_base.product_category_components"): ProductTypeEnum.COMPONENT,
        }
        return mapping.get(product.categ_id, None)

    @staticmethod
    def resolve_options(product, _):
        options = (
            product.sudo()
            .with_context(encode_full_product_configuration=True)
            .get_encoded_options()
        )
        # Build the relations
        relations = []
        for relation_result in options:
            # Group the options by relations
            options = []
            for selection in relation_result.get("selections", []):
                # Convert the current Rabbit representation of `onlogic_company` a.k.a `site`
                for field_name in ["is_default", "enabled"]:
                    for value in selection.get(field_name, []):
                        company_short_name = value.pop("onlogic_company", None)
                        value["onlogic_company"] = (
                            CompanyEnum(company_short_name).name or None
                        )

                options.append(
                    ProductConfigurationOption(
                        selection.get("default_qty", None),
                        selection.get("is_default", None),
                        selection.get("enabled", None),
                        True,
                        selection.get("max_qty", None),
                        selection.get("uuid", None),
                        selection.get("visible_to_user", None),
                    )
                )
            relations.append(
                ProductConfigurationRelation(
                    relation_result.get("classification", None),
                    relation_result.get("name", None),
                    relation_result.get("position", None),
                    relation_result.get("required", None),
                    options,
                    relation_result.get("uuid", None),
                )
            )

        return relations

    # Company dependent fields

    @staticmethod
    def resolve_active(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="sale_ok"
        )

    @staticmethod
    def resolve_lifecycle_status(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="lifecycle_status"
        )

    @staticmethod
    def resolve_base_price(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="list_price"
        )

    @staticmethod
    def resolve_special_price(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="list_price"
        )

    @staticmethod
    def resolve_product_tax_code(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="uuid", relations="tax_code_id"
        )

    @staticmethod
    def resolve_sku(product, _):
        return product.default_code or None

    @staticmethod
    def resolve_description(product, _):
        return product.description or None
