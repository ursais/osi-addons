# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import Form

# pylint: disable=odoo-addons-relative-import
from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaStockAccount(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.g_account_user = cls.env.ref("account.group_account_user")
        cls.rma_refund_wiz = cls.env["rma.refund"]
        # we create new products to ensure previous layers do not affect when
        # running FIFO
        cls.product_fifo_1 = cls._create_product("product_fifo1")
        cls.product_fifo_2 = cls._create_product("product_fifo2")
        cls.product_fifo_3 = cls._create_product("product_fifo3")
        # Refs
        cls.rma_operation_customer_refund_id = cls.env.ref(
            "rma_account.rma_operation_customer_refund"
        )
        cls.rma_basic_user.write({"groups_id": [(4, cls.g_account_user.id)]})
        cls.customer_route = cls.env.ref("rma.route_rma_customer")
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.output_location = cls.env.ref("stock.stock_location_output")
        # The product category created in the base module is not automated valuation
        # we have to create a new category here
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account("equity", name, code, cls.company, True)
        # Create account for Goods Delievered
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        cls.account_gdni = cls._create_account(
            "asset_current", name, code, cls.company, True
        )
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            "asset_current", name, code, cls.company, False
        )
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_valuation": "real_time",
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_stock_account_output_categ_id": cls.account_gdni.id,
                "rma_approval_policy": "one_step",
                "rma_customer_operation_id": cls.rma_operation_customer_refund_id.id,
                "rma_supplier_operation_id": cls.rma_sup_replace_op_id.id,
                "property_cost_method": "fifo",
            }
        )
        # We use FIFO to test the cost is taken from the original layers
        cls.product_fifo_1.categ_id = product_ctg
        cls.product_fifo_2.categ_id = product_ctg
        cls.product_fifo_3.categ_id = product_ctg

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile):
        """Create an account."""
        account = cls.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_id": company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def check_accounts_used(
        self, account_move, debit_account=False, credit_account=False
    ):
        debit_line = account_move.mapped("line_ids").filtered(lambda line: line.debit)
        credit_line = account_move.mapped("line_ids").filtered(lambda line: line.credit)
        if debit_account:
            self.assertEqual(debit_line.account_id[0].code, debit_account)
        if credit_account:
            self.assertEqual(credit_line.account_id[0].code, credit_account)

    def test_01_cost_from_standard(self):
        """
        Test the price unit is taken from the standard cost when there is no reference
        """
        self.product_fifo_1.standard_price = 15
        rma_line = Form(self.rma_line.with_user(self.rma_basic_user))
        rma_line.partner_id = self.partner_id
        rma_line.product_id = self.product_fifo_1
        rma_line.price_unit = 1234
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._receive_rma(rma_line)
        self.assertEqual(
            picking.move_line_ids.move_id.stock_valuation_layer_ids.value, 15.0
        )
        account_move = (
            picking.move_line_ids.move_id.stock_valuation_layer_ids.account_move_id
        )
        self.check_accounts_used(
            account_move, debit_account="inventory", credit_account="gdni"
        )

    def test_02_cost_from_move(self):
        """
        Test the price unit is taken from the cost of the stock move when the
        reference is the stock move
        """
        # Set a standard price on the products
        self.product_fifo_1.standard_price = 10
        self.product_fifo_2.standard_price = 20
        self.product_fifo_3.standard_price = 30
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        products2move = [
            (self.product_fifo_1, 3),
            (self.product_fifo_2, 5),
            (self.product_fifo_3, 2),
        ]
        rma_customer_id = self._create_rma_from_move(
            products2move,
            "customer",
            self.env.ref("base.res_partner_2"),
            dropship=False,
        )
        # Set an incorrect price in the RMA (this should not affect cost)
        rma_lines = rma_customer_id.rma_line_ids
        rma_lines.price_unit = 999
        rma_lines.action_rma_to_approve()
        picking = self._receive_rma(rma_customer_id.rma_line_ids)
        # Test the value in the layers of the incoming stock move is used
        for rma_line in rma_customer_id.rma_line_ids:
            value_origin = rma_line.reference_move_id.stock_valuation_layer_ids.value
            move_product = picking.move_line_ids.filtered(
                lambda line, rma_line=rma_line: line.product_id == rma_line.product_id
            )
            value_used = move_product.move_id.stock_valuation_layer_ids.value
            self.assertEqual(value_used, -value_origin)
        # Create a refund for the first line
        rma = rma_lines[0]
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.item_ids.qty_to_refund = 1
        make_refund.invoice_refund()
        rma.refund_line_ids.move_id.action_post()
        rma._compute_refund_count()
        gdni_amls = rma.refund_line_ids.move_id.line_ids.filtered(
            lambda line: line.account_id == self.account_gdni
        )
        gdni_amls |= (
            rma.move_ids.stock_valuation_layer_ids.account_move_id.line_ids.filtered(
                lambda line: line.account_id == self.account_gdni
            )
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        # When we received we Credited to GDNI 30
        # When we refund we Debit to GDNI 10
        self.assertEqual(gdni_balance, -20.0)
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.item_ids.qty_to_refund = 2
        make_refund.invoice_refund()
        rma.refund_line_ids.move_id.filtered(
            lambda m: m.state != "posted"
        ).action_post()
        rma._compute_refund_count()
        gdni_amls = rma.refund_line_ids.move_id.line_ids.filtered(
            lambda line: line.account_id == self.account_gdni
        )
        gdni_amls |= (
            rma.move_ids.stock_valuation_layer_ids.account_move_id.line_ids.filtered(
                lambda line: line.account_id == self.account_gdni
            )
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        # When we received we Credited to GDNI 30
        # When we refund we Debit to GDNI 30
        self.assertEqual(gdni_balance, 0.0)
        # Ensure that the GDNI move lines are all reconciled
        self.assertEqual(all(gdni_amls.mapped("reconciled")), True)

    def test_03_cost_from_move(self):
        """
        Receive a product and then return it. The Goods Delivered Not Invoiced
        should result in 0
        """
        # Set a standard price on the products
        self.product_fifo_1.standard_price = 10
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        products2move = [
            (self.product_fifo_1, 3),
        ]
        self.product_fifo_1.categ_id.rma_customer_operation_id = (
            self.rma_cust_replace_op_id
        )
        rma_customer_id = self._create_rma_from_move(
            products2move,
            "customer",
            self.env.ref("base.res_partner_2"),
            dropship=False,
        )
        # Set an incorrect price in the RMA (this should not affect cost)
        rma = rma_customer_id.rma_line_ids
        rma.price_unit = 999
        rma.action_rma_to_approve()
        self._receive_rma(rma_customer_id.rma_line_ids)
        gdni_amls = (
            rma.move_ids.stock_valuation_layer_ids.account_move_id.line_ids.filtered(
                lambda line: line.account_id == self.account_gdni
            )
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        self.assertEqual(len(gdni_amls), 1)
        # Balance should be -30, as we have only received
        self.assertEqual(gdni_balance, -30.0)
        self._deliver_rma(rma_customer_id.rma_line_ids)
        gdni_amls = (
            rma.move_ids.stock_valuation_layer_ids.account_move_id.line_ids.filtered(
                lambda line: line.account_id == self.account_gdni
            )
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        self.assertEqual(len(gdni_amls), 2)
        # Balance should be 0, as we have received and shipped
        self.assertEqual(gdni_balance, 0.0)
        # The GDNI entries should be now reconciled
        self.assertEqual(all(gdni_amls.mapped("reconciled")), True)

    def test_08_cost_from_move_multi_step(self):
        """
        Receive a product and then return it using a multi-step route.
        The Goods Delivered Not Invoiced should result in 0
        """
        # Alter the customer RMA route to make it multi-step
        # Get rid of the duplicated rule
        self.env.ref("rma.rule_rma_customer_out_pull").active = False
        self.env.ref("rma.rule_rma_customer_in_pull").active = False
        cust_in_pull_rule = self.customer_route.rule_ids.filtered(
            lambda r: r.location_dest_id == self.stock_rma_location
        )
        cust_in_pull_rule.location_dest_id = self.input_location
        cust_out_pull_rule = self.customer_route.rule_ids.filtered(
            lambda r: r.location_src_id == self.env.ref("rma.location_rma")
        )
        cust_out_pull_rule.location_src_id = self.output_location
        cust_out_pull_rule.procure_method = "make_to_order"
        self.env["stock.rule"].create(
            {
                "name": "RMA->Output",
                "action": "pull",
                "warehouse_id": self.wh.id,
                "location_src_id": self.env.ref("rma.location_rma").id,
                "location_dest_id": self.output_location.id,
                "procure_method": "make_to_stock",
                "route_id": self.customer_route.id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
            }
        )
        self.env["stock.rule"].create(
            {
                "name": "Customers->RMA",
                "action": "pull",
                "warehouse_id": self.wh.id,
                "location_src_id": self.customer_location.id,
                "location_dest_id": self.env.ref("rma.location_rma").id,
                "procure_method": "make_to_order",
                "route_id": self.customer_route.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
            }
        )
        # Set a standard price on the products
        self.product_fifo_1.standard_price = 10
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        products2move = [
            (self.product_fifo_1, 3),
        ]
        self.product_fifo_1.categ_id.rma_customer_operation_id = (
            self.rma_cust_replace_op_id
        )
        rma_customer_id = self._create_rma_from_move(
            products2move,
            "customer",
            self.env.ref("base.res_partner_2"),
            dropship=False,
        )
        # Set an incorrect price in the RMA (this should not affect cost)
        rma = rma_customer_id.rma_line_ids
        rma.price_unit = 999
        rma.action_rma_to_approve()
        self._receive_rma(rma)
        layers = rma.move_ids.sudo().stock_valuation_layer_ids
        gdni_amls = layers.account_move_id.line_ids.filtered(
            lambda line: line.account_id == self.account_gdni
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        self.assertEqual(len(gdni_amls), 1)
        # Balance should be -30, as we have only received
        self.assertEqual(gdni_balance, -30.0)
        self._deliver_rma(rma)
        layers = rma.move_ids.sudo().stock_valuation_layer_ids
        gdni_amls = layers.account_move_id.line_ids.filtered(
            lambda line: line.account_id == self.account_gdni
        )
        gdni_balance = sum(gdni_amls.mapped("balance"))
        self.assertEqual(len(gdni_amls), 2)
        # Balance should be 0, as we have received and shipped
        self.assertEqual(gdni_balance, 0.0)
        # The GDNI entries should be now reconciled
        self.assertEqual(all(gdni_amls.mapped("reconciled")), True)

    def test_05_reconcile_grni_when_no_refund(self):
        """
        Test that receive and send a replacement order leaves GDNI reconciled
        """
        self.product_fifo_1.standard_price = 15
        rma_line = Form(self.rma_line)
        rma_line.partner_id = self.partner_id
        rma_line.product_id = self.product_fifo_1
        rma_line.operation_id.automated_refund = True
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        # receiving should trigger the refund at zero cost
        self._receive_rma(rma_line)
        gdni_amls = self.env["account.move.line"].search(
            [
                ("rma_line_id", "in", rma_line.ids),
                ("account_id", "=", self.account_gdni.id),
            ]
        ) + rma_line.refund_line_ids.filtered(
            lambda line: line.account_id == self.account_gdni
        )
        self.assertEqual(all(gdni_amls.mapped("reconciled")), True)
