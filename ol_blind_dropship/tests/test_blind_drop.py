# Import Python libs
import logging
# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class TestBlindDrop(TransactionCase):
    """
    This is a simple test for the computed function defined for `stock.picking`
    """

    def setUp(self):
        super().setUp()

        # self.blind_product = self.env.ref("ol_blind_dropship.blind_drop_ship_product")
        self.blind_product = self.env["product.product"].create(
            {
                "name": "Product to indicate blind drop shipping",
                "type": "service",
                "default_code": "BLIND DROP SHIP PRODUCT",
                "categ_id": self.env.ref("product.product_category_3").id,
            }
        )

        self.company_id = self.browse_ref("base.main_company")
        self.warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_id.id)]
        )
        self.stock_location = self.warehouse.lot_stock_id
        self.customer_location = self.browse_ref("stock.stock_location_customers")
        self.partner = self.env["res.partner"].create(
            {
                "name": "Joshua Wood",
                "company_type": "person",
                "email": "jw@example.com",
            }
        )

    def _create_basic_sale_order(self, partner, product, product_qty, price_unit):
        return self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "pricelist_id": partner.property_product_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": product.id,
                            "product_uom_qty": product_qty,
                            "product_uom": product.uom_id.id,
                            "price_unit": price_unit,
                        },
                    )
                ],
            }
        )

    def test_blind_sku_in_order_line(self):
        """
        Make sure that pickings are marked if the blind drop sku
        is one of the sale lines
        """

        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.ref("stock.picking_type_out"),
                "partner_id": self.partner.id,
            }
        )

        # make sure the blind product is correctly set
        self.env["ir.config_parameter"].sudo().set_param(
            "stock_move.blind_drop_ship", self.blind_product.id
        )
        self.assertEqual(
            str(self.blind_product.id),
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("stock_move.blind_drop_ship"),
            "Blind product setting is not correct",
        )

        blind_order = self._create_basic_sale_order(
            partner=self.partner,
            product=self.blind_product,
            product_qty=10,
            price_unit=250,
        )

        self.assertFalse(
            picking.blind_drop_ship,
            "Stock Picking was incorrectly marked as Blind Drop!",
        )

        # Link the picking to a sale order for a blind drop product
        picking.sale_id = blind_order
        self.assertTrue(
            picking.blind_drop_ship, "Stock Picking was not marked as Blind Drop!"
        )

    # def test_blind_sku_in_system(self):
    #     """
    #     Make sure that pickings are marked if the blind drop sku is in the Bill of Materials
    #     """
    #     picking = self.env["stock.picking"].create(
    #         {
    #             "location_id": self.stock_location.id,
    #             "location_dest_id": self.customer_location.id,
    #             "picking_type_id": self.ref("stock.picking_type_out"),
    #             "partner_id": self.partner.id,
    #         }
    #     )
    #
    #     blind_order = self._create_system_sale_order(partner=self.partner)
    #
    #     # set one of the products in the BoM to be the blind ship product
    #     line_products = blind_order.order_line.product_id
    #     bom_products = blind_order.order_line.bom_id.bom_line_ids.product_id
    #
    #     # pick a bom product that is not on a different sale order line
    #     component = (bom_products - line_products)[0]
    #
    #     # Set our product to be the blind drop product
    #     _logger.debug(
    #         f"Set BoM component to be blind ship product: {component.default_code} ({component})"
    #     )
    #     self.env["ir.config_parameter"].sudo().set_param(
    #         "stock_move.blind_drop_ship", component.id
    #     )
    #     self.assertEqual(
    #         str(component.id),
    #         self.env["ir.config_parameter"]
    #         .sudo()
    #         .get_param("stock_move.blind_drop_ship"),
    #         "Blind product setting is not correct",
    #     )
    #
    #     self.assertFalse(
    #         picking.blind_drop_ship,
    #         "Stock Picking was incorrectly marked as Blind Drop!",
    #     )
    #
    #     # Link the picking to a sale order for a blind drop product
    #     picking.sale_id = blind_order
    #     self.assertTrue(
    #         picking.blind_drop_ship, "Stock Picking was not marked as Blind Drop!"
    #     )
    #
    #
    #
    # def _create_system_sale_order(self, partner):
    #     return self.env["sale.order"].create(
    #         {
    #             "partner_id": partner.id,
    #             "pricelist_id": partner.property_product_pricelist.id,
    #             # "order_line": [
    #             #     (
    #             #         0,
    #             #         0,
    #             #         {
    #             #             "name": "Test line",
    #             #             "product_id": product.id,
    #             #             "product_uom_qty": product_qty,
    #             #             "product_uom": product.uom_id.id,
    #             #             "price_unit": price_unit,
    #             #         },
    #             #     )
    #             # ],
    #         }
    #     )