# Copyright 2017-22 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestAccountMoveLineRmaOrderLine(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rma_model = cls.env["rma.order"]
        cls.rma_line_model = cls.env["rma.order.line"]
        cls.rma_refund_wiz = cls.env["rma.refund"]
        cls.rma_add_stock_move = cls.env["rma_add_stock_move"]
        cls.rma_make_picking = cls.env["rma_make_picking.wizard"]
        cls.invoice_model = cls.env["account.move"]
        cls.stock_picking_model = cls.env["stock.picking"]
        cls.invoice_line_model = cls.env["account.move.line"]
        cls.product_model = cls.env["product.product"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.account_model = cls.env["account.account"]
        cls.aml_model = cls.env["account.move.line"]
        cls.res_users_model = cls.env["res.users"]

        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.company = cls.env.ref("base.main_company")
        cls.group_rma_user = cls.env.ref("rma.group_rma_customer_user")
        cls.group_account_invoice = cls.env.ref("account.group_account_invoice")
        cls.group_account_manager = cls.env.ref("account.group_account_manager")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        wh = cls.env.ref("stock.warehouse0")
        cls.stock_rma_location = wh.lot_rma_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account("equity", name, code, cls.company)

        # Create account for Cost of Goods Sold
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        cls.account_cogs = cls._create_account("expense", name, code, cls.company)
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            "asset_current", name, code, cls.company
        )  # TODO: poner asset de inventario
        # Create Product
        cls.product = cls._create_product()
        cls.product_uom_id = cls.env.ref("uom.product_uom_unit")
        # Create users
        cls.rma_user = cls._create_user(
            "rma_user", [cls.group_rma_user, cls.group_account_invoice], cls.company
        )
        cls.account_invoice = cls._create_user(
            "account_invoice", [cls.group_account_invoice], cls.company
        )
        cls.account_manager = cls._create_user(
            "account_manager", [cls.group_account_manager], cls.company
        )

    @classmethod
    def _create_user(cls, login, groups, company):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = cls.res_users_model.with_context(**{"no_reset_password": True}).create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user.id

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile=False):
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

    @classmethod
    def _create_product(cls):
        """Create a Product."""
        #        group_ids = [group.id for group in groups]
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_valuation": "real_time",
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_stock_account_output_categ_id": cls.account_cogs.id,
            }
        )
        product = cls.product_model.create(
            {
                "name": "test_product",
                "categ_id": product_ctg.id,
                "type": "product",
                "standard_price": 1.0,
                "list_price": 1.0,
            }
        )
        return product

    @classmethod
    def _create_picking(cls, partner):
        return cls.stock_picking_model.create(
            {
                "partner_id": partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.supplier_location.id,
            }
        )

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        res = {
            "partner_id": cls.partner1.id,
            "product_id": product.id,
            "name": product.partner_ref,
            "state": "confirmed",
            "product_uom": cls.product_uom_id.id or product.uom_id.id,
            "product_uom_qty": qty,
            "origin": "Test RMA",
            "location_id": src.id,
            "location_dest_id": dest.id,
            "picking_id": picking_in.id,
        }
        return res

    @classmethod
    def _create_rma(cls, products2move, partner):
        picking_in = cls._create_picking(partner)
        moves = []
        for item in products2move:
            move_values = cls._prepare_move(
                item[0], item[1], cls.stock_location, cls.customer_location, picking_in
            )
            moves.append(cls.env["stock.move"].create(move_values))

        rma_id = cls.rma_model.create(
            {
                "reference": "0001",
                "type": "customer",
                "partner_id": partner.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        for move in moves:
            wizard = cls.rma_add_stock_move.new(
                {
                    "move_ids": [(6, 0, move.ids)],
                    "rma_id": rma_id.id,
                    "partner_id": move.partner_id.id,
                }
            )
            # data = wizard._prepare_rma_line_from_stock_move(move)
            wizard.add_lines()

            # CHECK ME: this code duplicate rma lines, what is the porpourse?
            # if move.product_id.rma_customer_operation_id:
            #     move.product_id.rma_customer_operation_id.in_route_id = False
            # move.product_id.categ_id.rma_customer_operation_id = False
            # move.product_id.rma_customer_operation_id = False
            # wizard._prepare_rma_line_from_stock_move(move)
            # cls.line = cls.rma_line_model.create(data)
        return rma_id

    def _get_balance(self, domain):
        """
        Call read_group method and return the balance of particular account.
        """
        aml_rec = self.aml_model.read_group(
            domain, ["debit", "credit", "account_id"], ["account_id"]
        )
        if aml_rec:
            return aml_rec[0].get("debit", 0) - aml_rec[0].get("credit", 0)
        else:
            return 0.0

    def _check_account_balance(self, account_id, rma_line=None, expected_balance=0.0):
        """
        Check the balance of the account
        """
        domain = [("account_id", "=", account_id)]
        if rma_line:
            domain.extend([("rma_line_id", "=", rma_line.id)])

        balance = self._get_balance(domain)
        if rma_line:
            self.assertEqual(
                balance,
                expected_balance,
                f"Balance is not {str(expected_balance)} for rma Line {rma_line.name}.",
            )

    def test_rma_invoice(self):
        """Test that the rma line moves from the rma order to the
        account move line and to the invoice line.
        """
        products2move = [
            (self.product, 1),
        ]
        rma = self._create_rma(products2move, self.partner1)
        rma_line = rma.rma_line_ids
        for rma in rma_line:
            if rma.price_unit == 0:
                rma.price_unit = 1.0
        rma_line.action_rma_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_id": 1,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
            }
        ).create({})
        operation = self.env["rma.operation"].search(
            [("type", "=", "customer"), ("refund_policy", "=", "received")], limit=1
        )
        rma_line.write({"operation_id": operation.id})
        rma_line.write({"refund_policy": "received"})

        wizard._create_picking()
        res = rma_line.action_view_in_shipments()
        if "res_id" in res:
            picking = self.env["stock.picking"].browse(res["res_id"])
        else:
            picking_ids = self.env["stock.picking"].search(res["domain"])
            picking = self.env["stock.picking"].browse(picking_ids)
        # picking.move_line_ids.write({"qty_done": 1.0})
        picking.button_validate()
        # decreasing cogs
        expected_balance = -1.0
        for record in rma_line:
            self._check_account_balance(
                self.account_cogs.id, rma_line=record, expected_balance=expected_balance
            )
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create(
            {
                "description": "Test refund",
            }
        )
        for item in make_refund.item_ids:
            item.write(
                {
                    "qty_to_refund": 1.0,
                }
            )
        make_refund.invoice_refund()
        rma_line.refund_line_ids.move_id.filtered(
            lambda x: x.state != "posted"
        ).action_post()
        for aml in rma_line.refund_line_ids.move_id.invoice_line_ids:
            if aml.product_id == rma_line.product_id and aml.move_id:
                self.assertEqual(
                    aml.rma_line_id,
                    rma_line,
                    "Rma Order line has not been copied from the invoice to "
                    "the account move line.",
                )
