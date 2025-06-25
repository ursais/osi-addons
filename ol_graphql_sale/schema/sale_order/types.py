# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import (
    OnLogicBaseObjectType,
    CompanyEnum,
    CompanyEnumType,
)
from odoo.addons.ol_graphql.schema.interface import BaseInterface
from odoo.addons.ol_graphql_partner.schema.res_partner.types import Partner
from odoo.addons.ol_graphql_sale.schema.sale_order_line.types import SaleOrderLine


class SaleOrder(OnLogicBaseObjectType, BaseInterface):
    """
    Graphene type for `sale.order` records
    """

    # accept_language = graphene.String() # TODO: waiting for OSI
    account_manager = graphene.Field(lambda: Partner)
    # active_exceptions = graphene.Boolean() # TODO: we need to reimplement this using the exception module. Waiting for OSI input
    # active_holds = graphene.Boolean() # TODO: should this go away now that holds are gone?
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    amount_untaxed = graphene.Float()
    billing_address = graphene.Field(lambda: Partner)
    commercial_partner_id = graphene.Field(lambda: Partner)
    # consumer_type = graphene.String() # TODO: waiting for OSI
    # coupon_code = graphene.String() # TODO: waiting for business input
    create_date = graphene.Date()
    customer_group = graphene.String()
    # customer_ip = graphene.String() # TODO: waiting for OSI
    # delivery_estimate = graphene.Date() # TODO: waiting for business input
    # detailed_state = graphene.String() # TODO: https://docs.google.com/spreadsheets/d/1cLI5TvL2AaxAKLJWA7DsziwYSpqGFIpA1hofdG22eBc/edit?gid=0#gid=0&range=K34 - waiting for business input
    # edit_date = graphene.Date() # TODO: waiting for business input
    # estimated_ship_date = graphene.Date() # TODO: waiting for OSI
    id = graphene.ID(required=True)
    # invoice_date = graphene.Date() # TODO: waiting for business input
    is_guest = graphene.Boolean()
    # is_quote = graphene.Boolean() # TODO: detailed_state is no more, now using substate_id. Waiting on OSI to finalize
    # lockdown = graphene.Boolean() # TODO: waiting for OSI
    name = graphene.String(required=True)
    onlogic_company = graphene.Field(CompanyEnumType, required=True)
    order_line = graphene.List(SaleOrderLine)
    # parent_order = graphene.ID() # TODO: waiting for business input
    partner_id = graphene.Field(lambda: Partner)
    # payment_method = GenericScalar() # TODO: need to implement this once OSI has payments setup
    po_number = graphene.String()
    shipping_address = graphene.Field(lambda: Partner)
    shipping_method = GenericScalar()
    state = graphene.String(required=True)
    tax_exemption_code = graphene.String()
    tax_exemption_number = graphene.String()
    # user_agent = graphene.String() # TODO: waiting for OSI
    user_id = graphene.Field(lambda: Partner)

    @staticmethod
    def resolve_account_manager(sale_order, _):
        return (
            sale_order.account_manager_id.partner_id
            if sale_order.account_manager_id
            else None
        )

    @staticmethod
    def resolve_amount_tax(sale_order, _):
        """
        If the Sale Order has any `has_import_tax_difference_holds` we should return the `ecommerce_total`
        if not we can return the amount total from Odoo.
        """
        if sale_order.has_import_tax_difference_holds():
            return sale_order.ecommerce_tax
        return sale_order.amount_tax

    @staticmethod
    def resolve_amount_total(sale_order, _):
        """
        If the Sale Order has any `has_import_tax_difference_holds` we should return the `ecommerce_total`
        if not we can return the amount total from Odoo.
        """
        if sale_order.has_import_tax_difference_holds():
            return sale_order.ecommerce_total
        return sale_order.amount_total

    @staticmethod
    def resolve_billing_address(sale_order, _):
        return sale_order.partner_invoice_id or None

    @staticmethod
    def resolve_commercial_partner_id(sale_order, _):
        return (
            sale_order.partner_id.commercial_partner_id
            if sale_order.partner_id.commercial_partner_id
            else None
        )

    @staticmethod
    def resolve_customer_group(sale_order, _):
        return (
            sale_order.pricelist_id.uuid
            if sale_order.pricelist_id and sale_order.pricelist_id.uuid
            else None
        )

    @staticmethod
    def resolve_is_guest(sale_order, _):
        return sale_order.is_guest_checkout or None

    @staticmethod
    def resolve_onlogic_company(odoo_record, _):
        return CompanyEnum(odoo_record.company_id.short_name)

    @staticmethod
    def resolve_order_line(sale_order, _):
        return [
            order_line
            for order_line in sale_order.order_line
            if not order_line.is_delivery
        ]

    @staticmethod
    def resolve_partner_id(sale_order, _):
        return sale_order.partner_id or None

    @staticmethod
    def resolve_po_number(sale_order, _):
        return sale_order.client_order_ref or None

    @staticmethod
    def resolve_shipping_address(sale_order, _):
        return sale_order.partner_shipping_id or None

    @staticmethod
    def resolve_shipping_method(sale_order, _):
        digits = (
            sale_order.env["decimal.precision"].sudo().precision_get("Product Price")
        )
        delivery_lines = sale_order.order_line.filtered(lambda r: r.is_delivery)
        price = sum(delivery_lines.mapped(lambda r: r.price_unit * r.product_uom_qty))
        price_tax = sum(delivery_lines.mapped("price_tax"))
        if not delivery_lines or not sale_order.carrier_id:
            return None
        if hasattr(sale_order.carrier_id, "uuid"):
            carrier_uuid = sale_order.carrier_id.uuid
        else:
            carrier_uuid = None
        return {
            "currency_code": sale_order.company_id.currency_id.name or None,
            "delivery_time": None,  # the website may send this
            "service_code": sale_order.carrier_id.message_code or None,
            "service_name": sale_order.carrier_id.name or None,
            "uuid": carrier_uuid,
            "price": round(price, digits),
            "price_tax": round(price_tax, digits),
        }

    @staticmethod
    def resolve_tax_exemption_code(sale_order, _):
        return sale_order.exemption_code_id.code or None

    @staticmethod
    def resolve_tax_exemption_number(sale_order, _):
        return sale_order.exemption_code or None

    @staticmethod
    def resolve_user_id(sale_order, _):
        return sale_order.user_id.partner_id if sale_order.user_id else None
