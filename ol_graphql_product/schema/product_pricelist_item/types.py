# Import Python Libs
from tokenize import group
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import (
    OnLogicBaseObjectType,
    CompanyEnum,
    CompanyEnumType,
)


class ProductPricelistItem(OnLogicBaseObjectType):
    """
    Graphene type for `product.pricelist.item` records
    """

    group = graphene.ID()
    group_name = graphene.String()
    percent = graphene.Float()
    price = graphene.Float()
    product = graphene.ID()
    quantity = graphene.Int()
    onlogic_company = graphene.Field(CompanyEnumType, required=True)
    type = graphene.String()

    @staticmethod
    def resolve_group(price_list_item, _):
        return (
            price_list_item.pricelist_id.uuid if price_list_item.pricelist_id else None
        )

    @staticmethod
    def resolve_group_name(price_list_item, _):
        return (
            price_list_item.pricelist_id.name if price_list_item.pricelist_id else None
        )

    @staticmethod
    def resolve_percent(price_list_item, _):
        return price_list_item.percent_price or None

    @staticmethod
    def resolve_price(price_list_item, _):
        return price_list_item.fixed_price or None

    @staticmethod
    def resolve_product(price_list_item, _):
        product = price_list_item.product_tmpl_id or price_list_item.product_id
        return product.uuid or None

    @staticmethod
    def resolve_quantity(price_list_item, _):
        return price_list_item.min_quantity or None

    @staticmethod
    def resolve_type(price_list_item, _):
        return price_list_item.compute_price or None

    @staticmethod
    def resolve_onlogic_company(price_list_item, _):
        return CompanyEnum(price_list_item.company_id.short_name)
