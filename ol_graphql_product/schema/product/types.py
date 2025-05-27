# Import Python Libs
import graphene
import datetime
from base64 import b64encode
from collections import defaultdict

# Import Odoo libs
from graphene.types.generic import GenericScalar
from odoo.addons.ol_graphql_product.schema.product.interface import (
    ProductTemplateInterface,
)
from odoo.addons.ol_graphql.tools import get_translated_field_values
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

    active = GenericScalar()
    attribute_set = graphene.String()
    # TODO: Evaluate with product assets
    # assets = GenericScalar()
    kit_components = GenericScalar()
    backorder_config = GenericScalar()
    can_sell = graphene.Boolean()
    companies = GenericScalar()
    description = graphene.String()
    # TODO: Evaluate with product assets
    # external_assets = GenericScalar()
    height = graphene.Float()
    length = graphene.Float()
    lifecycle_status = GenericScalar()
    width = graphene.Float()
    weight = graphene.Float()
    public_destination = graphene.String()
    sku = graphene.String(required=True)
    type = graphene.Field(ProductTypeEnum)
    message_source = graphene.String()
    name = GenericScalar()
    options = graphene.List(ProductConfigurationRelation)
    image = GenericScalar()
    system_stock_state = GenericScalar()
    website_system_stock_state = GenericScalar()

    # Pricing fields
    special_price = GenericScalar()
    base_price = GenericScalar()
    pricing_tiers = graphene.List(ProductPricelistItem)

    pim_attributes = graphene.Field(
        GenericScalar,
        attributes=graphene.List(
            graphene.String,
            default_value=None,
            description=(
                "List of attribute.attribute record names to fetch values for. If unspecified, "
                "attributes associated with the product's attribute set will be returned."
            ),
        ),
    )

    @staticmethod
    def resolve_image(product, _):
        if not product.image_1920:
            return None
        # Encode the image in base64
        image_encoded = b64encode(product.image_1920).decode("utf-8")
        return image_encoded

    @staticmethod
    def resolve_active(product, _):
        return product.sale_ok or None

    @staticmethod
    def resolve_can_sell(product, _):
        return product.sale_ok_confirm or None

    @staticmethod
    def resolve_attribute_set(product, _):
        if not product.attribute_set_id:
            return None

        return get_translated_field_values(
            odoo_record=product.attribute_set_id,
            field="name",
        )

    @staticmethod
    def resolve_message_source(product, _):
        return "ODOO"

    @staticmethod
    def resolve_companies(product, _):
        enabled_in_website = [
            company.short_name.upper() for company in product.company_ids
        ]
        return enabled_in_website or None

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
    def resolve_height(product, _):
        return product.product_height or None

    @staticmethod
    def resolve_length(product, _):
        return product.product_length or None

    @staticmethod
    def resolve_width(product, _):
        return product.product_width or None

    @staticmethod
    def resolve_lifecycle_status(product, _):
        if not product.product_state_id:
            return None

        return get_translated_field_values(
            odoo_record=product.product_state_id,
            field="name",
        )

    @staticmethod
    def resolve_name(product, _):
        name = get_translated_field_values(
            odoo_record=product,
            field="name",
        )
        return name or None

    @staticmethod
    def resolve_options(product, _):
        options = product.with_context(
            encode_full_product_configuration=True
        ).get_encoded_options()
        return [option for option in options]

    @staticmethod
    def resolve_kit_components(product, _):
        """
        This resolver fetches all active Phantom BoMs for the product, and returns the
        component uuid and qty of the most recently created one.
        """
        # Find the most recently created Phantom BoM
        phantom_bom_ids = product.bom_ids.filtered(
            lambda bom: bom.type == "phantom"
        ).sorted(key=lambda bom: bom.create_date, reverse=True)
        kit_components = []

        if phantom_bom_ids:
            phantom_bom_id = phantom_bom_ids[0]
            for bom_line in phantom_bom_id.bom_line_ids:
                product_id = bom_line.product_tmpl_id or bom_line.product_id
                kit_components.append(
                    {
                        "uuid": product_id.uuid if product_id else None,
                        "qty": bom_line.product_qty or None,
                    }
                )
        return kit_components

    # Company dependent fields

    @staticmethod
    def resolve_base_price(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="list_price"
        )

    @staticmethod
    def resolve_backorder_config(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="allow_backorder"
        )

    @staticmethod
    def resolve_special_price(product, _):
        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="special_price"
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

    @staticmethod
    def resolve_pricing_tiers(product, _):
        return product.pricelist_item_ids or None

    @staticmethod
    def resolve_system_stock_state(product, _):
        if product.is_stockable():
            # Return None if the product is not stockable
            return None

        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="system_stock_state"
        )

    @staticmethod
    def resolve_website_system_stock_state(product, _):
        if product.is_stockable():
            # Return None if the product is not stockable
            return None

        return ProductTemplate.get_company_dependent_field_value(
            base_record=product, field_name="website_system_stock_state"
        )

    # === BEGIN PIM ATTRIBUTE FUNCTIONS === #

    @classmethod
    def resolve_pim_attributes(cls, product, info, attributes=False):
        """
        Resolver for fetching PIM attributes

        Either fetches all attributes associated with the product's attribute set,
        or the list of attributes specified in the `attributes` argument.
        """
        if attributes:
            attribute_records = product.env["attribute.attribute"].search(
                [("name", "in", attributes)]
            )
            missing_attributes = set(attributes) - set(attribute_records.mapped("name"))
            if missing_attributes:
                raise ValueError(
                    f"GraphQL Query | Product: {product.default_code} (uuid: {product.uuid}) | The following attributes could not be found: {', '.join(missing_attributes)}"
                )

        else:
            if product.attribute_set_id and product.attribute_set_id.attribute_ids:
                attribute_records = product.attribute_set_id.attribute_ids
            else:
                raise ValueError(
                    f"GraphQL Query | Product: {product.default_code} (uuid: {product.uuid}) | No attribute set defined on product"
                )

        pim_attributes = {}
        for attribute in attribute_records:
            if attribute.attribute_type == "select":
                option = getattr(product, attribute.name)
                # Code is not a translated value
                code = option.code or ""
                attribute_values = get_translated_field_values(
                    odoo_record=option,
                    field="name",
                )
                for translation in attribute_values:
                    translation["code"] = code

            elif attribute.attribute_type == "multiselect":
                attribute_values = ProductTemplate.resolve_multiselect_pim_attribute(
                    product, attribute
                )

            elif attribute.attribute_type in ("text", "char"):
                attribute_values = get_translated_field_values(
                    odoo_record=product,
                    field=attribute.name,
                )
            else:
                attribute_values = getattr(product, attribute.name)
                if isinstance(attribute_values, datetime.date):
                    attribute_values = attribute_values.strftime("%Y-%m-%d")

            attribute_name = attribute.name
            # We could assume that all attributes are prefixed with `x_` as that is how core Odoo handles this field, but we verify to be safe
            if attribute_values and attribute_name.startswith("x_"):
                attribute_name = attribute_name[2:]
                pim_attributes[attribute_name] = attribute_values

        return pim_attributes or None

    def resolve_multiselect_pim_attribute(product, attribute):
        """
        This is handled outside of the "get_translated_field_values" method
        in order to retrieve the translations as an array
        """
        attribute_values = []
        options = getattr(product, attribute.name)

        # Code is not a translated value
        code_arr = [option.code or "" for option in options]

        langs = product.env["res.lang"].get_installed()
        for lang in langs:
            locale_attributes = {}
            locale_attributes["locale"] = lang[0]
            locale_attributes["label"] = [
                option.name or "" for option in options.with_context(lang=lang[0])
            ]
            locale_attributes["code"] = code_arr
            attribute_values.append(locale_attributes)
        return attribute_values or None

    # === END PIM ATTRIBUTE FUNCTIONS === #
