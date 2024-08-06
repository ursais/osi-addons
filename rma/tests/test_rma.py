# © 2017 ForgeFlow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, common


class TestRma(common.TransactionCase):
    """Test the routes and the quantities"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # models
        cls.rma_make_picking = cls.env["rma_make_picking.wizard"]
        cls.make_supplier_rma = cls.env["rma.order.line.make.supplier.rma"]
        cls.rma_add_stock_move = cls.env["rma_add_stock_move"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.stockpicking = cls.env["stock.picking"]
        cls.rma = cls.env["rma.order"]
        cls.rma_line = cls.env["rma.order.line"]
        cls.rma_op = cls.env["rma.operation"]
        cls.product_product_model = cls.env["product.product"]
        cls.res_users_model = cls.env["res.users"]
        # References and records
        cls.rma_cust_replace_op_id = cls.env.ref("rma.rma_operation_customer_replace")
        cls.rma_sup_replace_op_id = cls.env.ref("rma.rma_operation_supplier_replace")
        cls.rma_ds_replace_op_id = cls.env.ref("rma.rma_operation_ds_replace")
        cls.category = cls._create_product_category(
            "one_step", cls.rma_cust_replace_op_id, cls.rma_sup_replace_op_id
        )
        cls.product_id = cls._create_product("PT0")
        cls.product_1 = cls._create_product("PT1")
        cls.product_2 = cls._create_product("PT2")
        cls.product_3 = cls._create_product("PT3")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.company = cls.env.company
        cls.company.group_rma_delivery_address = True
        cls.company.group_rma_lines = True

        cls.partner_id = cls.env.ref("base.res_partner_2")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.stock_rma_location = cls.wh.lot_rma_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.product_uom_id = cls.env.ref("uom.product_uom_unit")
        cls.g_rma_customer_user = cls.env.ref("rma.group_rma_customer_user")
        cls.g_rma_supplier_user = cls.env.ref("rma.group_rma_supplier_user")
        cls.g_rma_manager = cls.env.ref("rma.group_rma_manager")
        cls.g_stock_user = cls.env.ref("stock.group_stock_user")
        cls.g_stock_manager = cls.env.ref("stock.group_stock_manager")

        cls.rma_basic_user = cls._create_user(
            "rma worker",
            [cls.g_stock_user, cls.g_rma_customer_user, cls.g_rma_supplier_user],
            cls.company,
        )
        cls.rma_manager_user = cls._create_user(
            "rma manager",
            [cls.g_stock_manager, cls.g_rma_manager],
            cls.company,
        )
        # Customer RMA:
        products2move = [(cls.product_1, 3), (cls.product_2, 5), (cls.product_3, 2)]
        cls.rma_customer_id = cls._create_rma_from_move(
            products2move, "customer", cls.env.ref("base.res_partner_2"), dropship=False
        )
        # Dropship:
        cls.rma_droship_id = cls._create_rma_from_move(
            products2move,
            "customer",
            cls.env.ref("base.res_partner_2"),
            dropship=True,
            supplier_address_id=cls.env.ref("base.res_partner_3"),
        )
        # Supplier RMA:
        cls.rma_supplier_id = cls._create_rma_from_move(
            products2move, "supplier", cls.env.ref("base.res_partner_2"), dropship=False
        )

    @classmethod
    def _create_user(cls, login, groups, company):
        group_ids = [group.id for group in groups]
        user = cls.res_users_model.create(
            {
                "name": login,
                "login": login,
                "email": "example@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    @classmethod
    def _receive_rma(cls, rma_line_ids):
        wizard = cls.rma_make_picking.with_context(
            **{
                "active_ids": rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        res = rma_line_ids.action_view_in_shipments()
        picking = cls.env["stock.picking"].browse(res["res_id"])
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity = mv.product_uom_qty
            mv.picked = True
        picking._action_done()
        return picking

    @classmethod
    def _deliver_rma(cls, rma_line_ids):
        wizard = cls.rma_make_picking.with_context(
            **{
                "active_ids": rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "outgoing",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        res = rma_line_ids.action_view_out_shipments()
        picking = cls.env["stock.picking"].browse(res["res_id"])
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity = mv.product_uom_qty
            mv.picked = True
        picking._action_done()
        return picking

    @classmethod
    def _create_product_category(
        cls, rma_approval_policy, rma_customer_operation_id, rma_supplier_operation_id
    ):
        return cls.product_ctg_model.create(
            {
                "name": "Test category",
                "rma_approval_policy": rma_approval_policy,
                "rma_customer_operation_id": rma_customer_operation_id.id,
                "rma_supplier_operation_id": rma_supplier_operation_id.id,
            }
        )

    @classmethod
    def _create_product(cls, name):
        return cls.product_product_model.create(
            {"name": name, "categ_id": cls.category.id, "type": "product"}
        )

    @classmethod
    def _create_picking(cls, partner, picking_type):
        return cls.stockpicking.create(
            {
                "partner_id": partner.id,
                "picking_type_id": picking_type.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.supplier_location.id,
            }
        )

    @classmethod
    def _do_picking(cls, picking):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_ids:
            ml.filtered(lambda m: m.state != "waiting").quantity = ml.product_uom_qty
            ml.filtered(lambda m: m.state != "waiting").picked = True
        picking.button_validate()

    @classmethod
    def _create_inventory(cls, product, qty, location):
        """
        Creates inventory of a product on a specific location, this will be used
        eventually to create a inventory at specific cost, that will be received in
        a customer RMA or delivered in a supplier RMA
        """
        inventory = (
            cls.env["stock.quant"]
            .create(
                {
                    "location_id": location.id,
                    "product_id": product.id,
                    "inventory_quantity": qty,
                }
            )
            .action_apply_inventory()
        )
        return inventory

    @classmethod
    def _get_picking_type(cls, wh, loc1, loc2):
        picking_type = cls.env["stock.picking.type"].search(
            [
                ("warehouse_id", "=", wh.id),
                ("default_location_src_id", "=", loc1.id),
                ("default_location_dest_id", "=", loc2.id),
            ],
            limit=1,
        )
        if picking_type:
            return picking_type
        picking_type = cls.env["stock.picking.type"].create(
            {
                "name": loc1.name + " to " + loc2.name,
                "sequence_code": loc1.name + " to " + loc2.name,
                "code": "incoming",
                "warehouse_id": wh.id,
                "default_location_src_id": loc1.id,
                "default_location_dest_id": loc2.id,
            }
        )
        return picking_type

    @classmethod
    def _create_rma_from_move(
        cls, products2move, r_type, partner, dropship, supplier_address_id=None
    ):
        moves = []
        if r_type == "customer":
            picking_type = cls._get_picking_type(
                cls.wh, cls.stock_location, cls.customer_location
            )
            picking = cls._create_picking(partner, picking_type)
            for item in products2move:
                product = item[0]
                product_qty = item[1]
                cls._create_inventory(product, product_qty, cls.stock_location)
                move_values = cls._prepare_move(
                    product,
                    product_qty,
                    cls.stock_location,
                    cls.customer_location,
                    picking,
                )
                moves.append(cls.env["stock.move"].create(move_values))
        else:
            picking_type = cls._get_picking_type(
                cls.wh, cls.supplier_location, cls.stock_rma_location
            )
            picking = cls._create_picking(partner, picking_type)
            for item in products2move:
                product = item[0]
                product_qty = item[1]
                cls._create_inventory(product, product_qty, cls.stock_location)
                move_values = cls._prepare_move(
                    product,
                    product_qty,
                    cls.supplier_location,
                    cls.stock_rma_location,
                    picking,
                )
                moves.append(cls.env["stock.move"].create(move_values))
        # Process the picking
        cls._do_picking(picking)
        # Create the RMA from the stock_move
        rma_id = cls.rma.with_user(cls.rma_basic_user).create(
            {
                "reference": "0001",
                "type": r_type,
                "partner_id": partner.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        for move in moves:
            if r_type == "customer":
                wizard = cls.rma_add_stock_move.with_user(cls.rma_basic_user).new(
                    {
                        "move_ids": [(4, move.id)],
                        "rma_id": rma_id.id,
                        "partner_id": move.partner_id.id,
                    }
                )
                wizard.with_context(
                    **{
                        "move_ids": [(4, move.id)],
                        "reference_move_id": move.id,
                        "customer": True,
                        "active_ids": rma_id.id,
                        "partner_id": move.partner_id.id,
                        "active_model": "rma.order",
                    }
                ).default_get([str(move.id), str(cls.partner_id.id)])
                data = (
                    wizard.with_user(cls.rma_basic_user)
                    .with_context(customer=1)
                    ._prepare_rma_line_from_stock_move(move)
                )

            else:
                wizard = cls.rma_add_stock_move.with_user(cls.rma_basic_user).new(
                    {
                        "move_ids": [(4, move.id)],
                        "rma_id": rma_id.id,
                        "partner_id": move.partner_id.id,
                    }
                )
                wizard.with_context(
                    **{
                        "move_ids": [(4, move.id)],
                        "reference_move_id": move.id,
                        "active_ids": rma_id.id,
                        "partner_id": move.partner_id.id,
                        "active_model": "rma.order",
                    }
                ).default_get([str(move.id), str(cls.partner_id.id)])
                data = wizard.with_user(
                    cls.rma_basic_user
                )._prepare_rma_line_from_stock_move(move)
                data["type"] = "supplier"
            if dropship:
                data.update(
                    customer_to_supplier=dropship,
                    operation_id=cls.rma_ds_replace_op_id.id,
                    supplier_address_id=supplier_address_id.id,
                )
            cls.line = cls.rma_line.with_user(cls.rma_basic_user).create(data)
            cls.line._onchange_product_id()
            cls.line._onchange_operation_id()
            cls.line.action_rma_to_approve()
        rma_id._get_default_type()
        rma_id.action_view_in_shipments()
        rma_id.action_view_out_shipments()
        rma_id.action_view_lines()
        rma_id.partner_id.action_open_partner_rma()
        return rma_id

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        location_id = src.id

        return {
            "name": product.name,
            "partner_id": picking_in.partner_id.id,
            "origin": picking_in.name,
            "company_id": picking_in.picking_type_id.warehouse_id.company_id.id,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "state": "draft",
            "product_uom_qty": qty,
            "location_id": location_id,
            "location_dest_id": dest.id,
            "picking_id": picking_in.id,
            "price_unit": product.standard_price,
        }

    def _check_equal_quantity(self, qty1, qty2, msg):
        self.assertEqual(qty1, qty2, msg)

    def test_01_rma_order_line(self):
        for line in self.rma_customer_id.rma_line_ids:
            line.with_context(
                **{"default_rma_id": line.rma_id.id}
            )._default_warehouse_id()
            line._default_location_id()
            line._onchange_delivery_address()
            line._compute_in_shipment_count()
            line._compute_out_shipment_count()

            # check assert if call reference_move_id onchange
            self.assertEqual(line.product_id, line.reference_move_id.product_id)
            self.assertEqual(line.product_qty, line.reference_move_id.product_uom_qty)
            self.assertEqual(
                line.location_id.location_id, line.reference_move_id.location_id
            )
            self.assertEqual(line.origin, line.reference_move_id.picking_id.name)
            self.assertEqual(
                line.delivery_address_id, line.reference_move_id.picking_id.partner_id
            )
            self.assertEqual(
                line.qty_to_receive, line.reference_move_id.product_uom_qty
            )
            line._onchange_product_id()
            line._onchange_operation_id()
            # check assert if call operation_id onchange
            self.assertEqual(line.operation_id.receipt_policy, line.receipt_policy)

            data = {"customer_to_supplier": line.customer_to_supplier}
            line = self.rma_line.new(data)
            line._onchange_receipt_policy()

            data = {"lot_id": line.lot_id.id}
            line = self.rma_line.new(data)
            line._onchange_lot_id()

            line.action_view_in_shipments()
            line.action_view_out_shipments()
            self.rma_customer_id.action_view_supplier_lines()
            with self.assertRaises(ValidationError):
                line.rma_id.partner_id = self.partner_id.id
                self.rma_customer_id.rma_line_ids[0].partner_id = self.env.ref(
                    "base.res_partner_3"
                ).id
        self.rma_customer_id.action_view_supplier_lines()

    def test_02_customer_rma(self):
        self.rma_customer_id.rma_line_ids.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": self.rma_customer_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_in_shipments()
        self.assertTrue("res_id" in res, "Incorrect number of pickings" "created")
        picking = self.env["stock.picking"].browse(res["res_id"])
        self.assertEqual(len(picking), 1, "Incorrect number of pickings created")
        moves = picking.move_ids
        self.assertEqual(len(moves), 3, "Incorrect number of moves created")
        lines = self.rma_customer_id.rma_line_ids
        lines.env.invalidate_all()
        self.assertEqual(
            list(set(lines.mapped("qty_received"))), [0], "Wrong qty received"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_to_deliver"))), [0], "Wrong qty to deliver"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_outgoing"))), [0], "Wrong qty outgoing"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_delivered"))), [0], "Wrong qty delivered"
        )
        self.assertEqual(
            sum(lines.mapped("in_shipment_count")), 3, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            sum(lines.mapped("out_shipment_count")), 0, "Incorrect Out Shipment Count"
        )
        self.assertEqual(
            self.rma_customer_id.in_shipment_count, 1, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            self.rma_customer_id.out_shipment_count, 0, "Incorrect Out Shipment Count"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_receive,
            3,
            "Wrong qty to receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_incoming,
            3,
            "Wrong qty incoming",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_receive,
            5,
            "Wrong qty to receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_incoming,
            5,
            "Wrong qty incoming",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_receive,
            2,
            "Wrong qty to receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_incoming,
            2,
            "Wrong qty incoming",
        )
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity = mv.product_uom_qty
            mv.picked = True
        picking._action_done()
        lines = self.rma_customer_id.rma_line_ids
        self.assertEqual(
            list(set(lines.mapped("qty_to_receive"))), [0], "Wrong qty to_receive"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty incoming"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_outgoing"))), [0], "Wrong qty outgoing"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_delivered"))), [0], "Wrong qty delivered"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_received,
            3,
            "Wrong qty received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_deliver,
            3,
            "Wrong qty to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_received,
            5,
            "Wrong qty received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_deliver,
            5,
            "Wrong qty to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_received,
            2,
            "Wrong qty received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_deliver,
            2,
            "Wrong qty to_deliver",
        )

        wizard = self.rma_make_picking.with_context(
            **{
                "active_id": 1,
                "active_ids": self.rma_customer_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "outgoing",
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_out_shipments()
        self.assertTrue("res_id" in res, "Incorrect number of pickings" "created")
        picking = self.env["stock.picking"].browse(res["res_id"])
        moves = picking.move_ids
        self.assertEqual(len(moves), 3, "Incorrect number of moves created")
        lines = self.rma_customer_id.rma_line_ids
        lines.env.invalidate_all()
        self.assertEqual(
            list(set(lines.mapped("qty_to_receive"))), [0], "Wrong qty to_receive"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty incoming"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_delivered"))), [0], "Wrong qty delivered"
        )
        self.assertEqual(
            sum(lines.mapped("in_shipment_count")), 3, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            sum(lines.mapped("out_shipment_count")),
            3,
            "Incorrect Out Shipment Count",
        )
        self.assertEqual(
            self.rma_customer_id.in_shipment_count, 1, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            self.rma_customer_id.out_shipment_count, 1, "Incorrect Out Shipment Count"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_deliver,
            3,
            "Wrong qty to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_outgoing,
            3,
            "Wrong qty outgoing",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_deliver,
            5,
            "Wrong qty to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_outgoing,
            5,
            "Wrong qty outgoing",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_deliver,
            2,
            "Wrong qty to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_outgoing,
            2,
            "Wrong qty outgoing",
        )
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity = mv.product_uom_qty
            mv.picked = True
        picking._action_done()
        lines = self.rma_customer_id.rma_line_ids
        self.assertEqual(
            list(set(lines.mapped("qty_to_receive"))), [0], "Wrong qty to_receive"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty incoming"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_outgoing"))), [0], "Wrong qty_outgoing"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_received,
            3,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_delivered,
            3,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_received,
            5,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_delivered,
            5,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_received,
            2,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_delivered,
            2,
            "Wrong qty_delivered",
        )
        self.rma_customer_id.rma_line_ids.action_rma_done()
        self.assertEqual(
            self.rma_customer_id.rma_line_ids.mapped("state"),
            ["done", "done", "done"],
            "Wrong State",
        )
        self.rma_customer_id.action_view_in_shipments()
        self.rma_customer_id.action_view_out_shipments()
        self.rma_customer_id.action_view_lines()

    # DROPSHIP
    def test_03_dropship(self):
        for line in self.rma_droship_id.rma_line_ids:
            line.operation_id = self.rma_ds_replace_op_id
            line._onchange_operation_id()
            line._onchange_delivery_address()
            line.action_rma_to_approve()
            line.action_rma_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_id": 1,
                "active_ids": self.rma_droship_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_droship_id.rma_line_ids.action_view_in_shipments()
        self.assertTrue("res_id" in res, "Incorrect number of pickings created")
        picking = self.env["stock.picking"].browse(res["res_id"])
        self.assertEqual(len(picking), 1, "Incorrect number of pickings created")
        moves = picking.move_ids
        self.assertEqual(len(moves), 3, "Incorrect number of moves created")
        lines = self.rma_droship_id.rma_line_ids
        lines.env.invalidate_all()
        self.assertEqual(
            sum(lines.mapped("in_shipment_count")), 3, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            sum(lines.mapped("out_shipment_count")), 0, "Incorrect Out Shipment Count"
        )
        self.assertEqual(
            self.rma_droship_id.in_shipment_count, 1, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            self.rma_droship_id.out_shipment_count, 0, "Incorrect Out Shipment Count"
        )
        wizard = self.make_supplier_rma.with_context(
            **{
                "active_ids": self.rma_droship_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "active_id": 1,
            }
        ).create({})
        wizard.make_supplier_rma()
        lines = self.rma_droship_id.rma_line_ids.mapped("supplier_rma_line_ids")
        lines.env.invalidate_all()
        self.assertEqual(
            list(set(lines.mapped("qty_received"))), [0], "Wrong qty_received"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_outgoing"))), [0], "Wrong qty_outgoing"
        )
        self.assertEqual(list(set(lines.mapped("qty_delivered"))), [0], "qty_delivered")
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_deliver,
            3,
            "Wrong qty_to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_deliver,
            5,
            "Wrong qty_to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_deliver,
            2,
            "Wrong qty_to_deliver",
        )
        lines = self.rma_droship_id.rma_line_ids
        lines.env.invalidate_all()
        self._check_equal_quantity(
            lines.filtered(
                lambda x: x.product_id == self.product_1
            ).qty_in_supplier_rma,
            3,
            "Wrong qty_in_supplier_rma",
        )
        self._check_equal_quantity(
            lines.filtered(
                lambda x: x.product_id == self.product_2
            ).qty_in_supplier_rma,
            5,
            "Wrong qty_in_supplier_rma",
        )
        self._check_equal_quantity(
            lines.filtered(
                lambda x: x.product_id == self.product_3
            ).qty_in_supplier_rma,
            2,
            "Wrong qty_in_supplier_rma",
        )
        self.assertEqual(
            list(set(lines.mapped("qty_to_supplier_rma"))),
            [0],
            "Wrong qty_to_supplier_rma",
        )
        for line in self.rma_droship_id.rma_line_ids:
            line.action_rma_done()
            self.assertEqual(line.mapped("state"), ["done"], "Wrong State")

    # Supplier RMA
    def test_04_supplier_rma(self):
        self.rma_supplier_id.rma_line_ids.action_rma_to_approve()
        self.rma_supplier_id.rma_line_ids.operation_id = self.rma_sup_replace_op_id
        self.rma_supplier_id.rma_line_ids._onchange_operation_id()
        self.rma_supplier_id.rma_line_ids._onchange_delivery_address()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": self.rma_supplier_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "outgoing",
                "active_id": 2,
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_supplier_id.rma_line_ids.action_view_out_shipments()
        self.assertTrue("res_id" in res, "Incorrect number of pickings" "created")
        picking = self.rma_supplier_id.rma_line_ids._get_out_pickings()
        partner = picking.partner_id
        self.assertTrue(partner, "Partner is not defined or False")
        moves = picking.move_ids
        self.assertEqual(len(moves), 3, "Incorrect number of moves created")

        lines = self.rma_supplier_id.rma_line_ids
        lines.env.invalidate_all()
        self.assertEqual(
            list(set(lines.mapped("qty_received"))), [0], "Wrong qty_received"
        )
        self.assertEqual(list(set(lines.mapped("qty_delivered"))), [0], "qty_delivered")
        self.assertEqual(
            sum(lines.mapped("in_shipment_count")), 0, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            sum(lines.mapped("out_shipment_count")), 3, "Incorrect Out Shipment Count"
        )
        self.assertEqual(
            self.rma_supplier_id.in_shipment_count, 0, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            self.rma_supplier_id.out_shipment_count, 1, "Incorrect Out Shipment Count"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_receive,
            3,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_deliver,
            3,
            "Wrong qty_to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_receive,
            5,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_deliver,
            5,
            "Wrong qty_to_deliver",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_receive,
            2,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_deliver,
            2,
            "Wrong qty_to_deliver",
        )
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty_incoming"
        )
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity = mv.product_uom_qty
            mv.picked = True
        picking._action_done()
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty_incoming"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_to_deliver"))), [0], "Wrong qty_to_deliver"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_received"))), [0], "Wrong qty_received"
        )
        self.assertEqual(list(set(lines.mapped("qty_outgoing"))), [0], "qty_outgoing")
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_delivered,
            3,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_receive,
            3,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_received,
            0,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_delivered,
            5,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_received,
            0,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_delivered,
            2,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_received,
            0,
            "Wrong qty_received",
        )
        wizard = self.rma_make_picking.with_context(
            **{
                "active_id": 1,
                "active_ids": self.rma_supplier_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_supplier_id.rma_line_ids.action_view_in_shipments()
        self.assertTrue("res_id" in res, "Incorrect number of pickings" "created")
        pickings = self.env["stock.picking"].browse(res["res_id"])
        self.assertEqual(len(pickings), 1, "Incorrect number of pickings created")
        picking_in = pickings[0]
        partner = picking_in.partner_id
        self.assertTrue(partner, "Partner is not defined or False")
        moves = picking.move_ids
        self.assertEqual(len(moves), 3, "Incorrect number of moves created")

        lines = self.rma_supplier_id.rma_line_ids
        lines.env.invalidate_all()
        self.assertEqual(
            list(set(lines.mapped("qty_to_deliver"))), [0], "qty_to_deliver"
        )
        self.assertEqual(
            sum(lines.mapped("in_shipment_count")), 3, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            sum(lines.mapped("out_shipment_count")), 3, "Incorrect Out Shipment Count"
        )
        self.assertEqual(
            self.rma_supplier_id.in_shipment_count, 1, "Incorrect In Shipment Count"
        )
        self.assertEqual(
            self.rma_supplier_id.out_shipment_count, 1, "Incorrect Out Shipment Count"
        )
        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_to_receive,
            3,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_to_receive,
            5,
            "Wrong qty_to_receive",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_to_receive,
            2,
            "Wrong qty_to_receive",
        )
        picking_in.action_confirm()
        picking_in.action_assign()
        for mv in picking_in.move_line_ids:
            mv.quantity = mv.quantity_product_uom
            mv.picked = True
        picking_in._action_done()
        self.assertEqual(
            list(set(lines.mapped("qty_outgoing"))), [0], "Wrong qty_outgoing"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_incoming"))), [0], "Wrong qty_incoming"
        )
        self.assertEqual(
            list(set(lines.mapped("qty_to_deliver"))), [0], "qty_to_deliver"
        )

        # product specific
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_delivered,
            3,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_1).qty_received,
            3,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_delivered,
            5,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_2).qty_received,
            5,
            "Wrong qty_received",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_delivered,
            2,
            "Wrong qty_delivered",
        )
        self._check_equal_quantity(
            lines.filtered(lambda x: x.product_id == self.product_3).qty_received,
            2,
            "Wrong qty_received",
        )
        for line in self.rma_supplier_id.rma_line_ids:
            line.action_rma_done()
            self.assertEqual(line.state, "done", "Wrong State")

    def test_05_rma_order_line(self):
        """Property rma_customer_operation_id on product or product category
        correctly handled inside _onchange_product_id()
        """
        rma_operation = self.env["rma.operation"].search([], limit=1)
        self.assertTrue(rma_operation)

        # Case of product template
        self.rma_customer_id.rma_line_ids.mapped("product_id").sudo().write(
            {"rma_customer_operation_id": rma_operation.id}
        )
        for line in self.rma_customer_id.rma_line_ids:
            data = {"product_id": line.product_id.id}
            new_line = self.rma_line.new(data)
            self.assertFalse(new_line.operation_id)
            self.assertTrue(new_line.product_id.rma_customer_operation_id)
            self.assertTrue(new_line.product_id.categ_id.rma_customer_operation_id)
            new_line._onchange_product_id()
            self.assertEqual(new_line.operation_id, rma_operation)

        # Case of product category
        self.rma_customer_id.rma_line_ids.mapped("product_id").sudo().write(
            {"rma_customer_operation_id": False}
        )
        self.rma_customer_id.rma_line_ids.mapped("product_id.categ_id").sudo().write(
            {"rma_customer_operation_id": rma_operation.id}
        )

        for line in self.rma_customer_id.rma_line_ids:
            data = {"product_id": line.product_id.id}
            new_line = self.rma_line.new(data)
            self.assertFalse(new_line.operation_id)
            self.assertFalse(new_line.product_id.rma_customer_operation_id)
            self.assertTrue(new_line.product_id.categ_id.rma_customer_operation_id)
            new_line._onchange_product_id()
            self.assertEqual(new_line.operation_id, rma_operation)

    def test_06_warehouse_mismatch(self):
        """Mismatch between operation warehouse and stock rule warehouse is raised.

        * Create a second warehouse that is resupplied from the main warehouse
        * Update an RMA to receive into the second warehouse
        * When creating pickings, it is raised that the rules from the RMA
        * config are not used.
        """
        wh2 = self.env["stock.warehouse"].create(
            {
                "name": "Shop.",
                "code": "SHP",
            }
        )
        wh2.resupply_wh_ids = self.env.ref("stock.warehouse0")
        wh2.rma_in_this_wh = True
        wh2.lot_rma_id = self.env["stock.location"].create(
            {
                "name": "WH2 RMA",
                "usage": "internal",
                "location_id": wh2.lot_stock_id.id,
            }
        )
        rma = self.rma_customer_id.copy()
        rma.rma_line_ids = self.rma_customer_id.rma_line_ids[0].copy()
        rma.rma_line_ids.product_id.sudo().route_ids += wh2.resupply_route_ids
        rma_form = Form(rma)
        rma_form.in_warehouse_id = wh2
        rma_form.save()
        rma.rma_line_ids.action_rma_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": rma.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        with self.assertRaisesRegex(UserError, "No rule found"):
            wizard._create_picking()

    def test_07_no_zero_qty_moves(self):
        rma_lines = self.rma_customer_id.rma_line_ids
        rma_lines.write({"receipt_policy": "delivered"})
        self.assertEqual(sum(rma_lines.mapped("qty_to_receive")), 0)
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": rma_lines.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        with self.assertRaisesRegex(ValidationError, "No quantity to transfer"):
            wizard._create_picking()

    def test_08_supplier_rma_single_line(self):
        rma_line_id = self.rma_supplier_id.rma_line_ids[0].id
        wizard = self.rma_make_picking.with_context(
            active_ids=[rma_line_id],
            active_model="rma.order.line",
            picking_type="outgoing",
            active_id=2,
        ).create({})
        wizard._create_picking()
        picking = self.rma_supplier_id.rma_line_ids[0]._get_out_pickings()
        partner = picking.partner_id
        self.assertTrue(partner, "Partner is not defined or False")
        moves = picking.move_ids
        self.assertEqual(len(moves), 1, "Incorrect number of moves created")

    def test_09_rma_state(self):
        rma = self.rma_customer_id
        self.assertEqual(rma.state, "approved")
        rma.rma_line_ids.action_rma_draft()
        self.assertEqual(rma.state, "draft")
        rma.action_rma_approve()
        self.assertEqual(
            rma.rma_line_ids.mapped("state"), ["approved", "approved", "approved"]
        )
