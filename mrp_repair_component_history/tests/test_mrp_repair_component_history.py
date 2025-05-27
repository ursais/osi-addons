# Import Odoo libs
from odoo.tests import common, tagged
from datetime import datetime


@tagged("-at_install", "post_install")
class TestComponentHistory(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.Lot = cls.env["stock.lot"]
        cls.Repair = cls.env["repair.order"]
        cls.RepairLine = cls.env["repair.line"]
        cls.ComponentHistory = cls.env["component.history"]
        cls.Manufacturing = cls.env["mrp.production"]
        cls.BoM = cls.env["mrp.bom"]
        cls.UoM = cls.env.ref("uom.product_uom_unit")

        # Base products
        cls.component = cls.Product.create({"name": "Component X", "type": "product"})
        cls.main_product = cls.Product.create(
            {
                "name": "Main Product",
                "type": "product",
                "tracking": "serial",
            }
        )

        # Lot for the main product
        cls.lot = cls.Lot.create(
            {
                "name": "SN001",
                "product_id": cls.main_product.id,
            }
        )

    def test_generate_add_and_remove_history(self):
        """Test that 'add' and 'remove' history lines cancel each other."""

        repair = self.Repair.create({"lot_id": self.lot.id})
        self.RepairLine.create(
            [
                {
                    "repair_id": repair.id,
                    "product_id": self.component.id,
                    "product_uom_qty": 2,
                    "repair_line_type": "add",
                },
                {
                    "repair_id": repair.id,
                    "product_id": self.component.id,
                    "product_uom_qty": 2,
                    "repair_line_type": "remove",
                },
            ]
        )

        self.lot.generate_component_history()

        history = self.ComponentHistory.search([("lot_id", "=", self.lot.id)])
        self.assertEqual(len(history), 2, "Should create 2 history records")

        visible = history.filtered(lambda h: not h.invisible)
        self.assertEqual(
            len(visible), 0, "Both records should be invisible after cancellation"
        )

    def test_partial_remove_creates_adjusted_add(self):
        """Test that a partial 'remove' hides original and creates reduced 'add'."""

        repair = self.Repair.create({"lot_id": self.lot.id})
        self.RepairLine.create(
            [
                {
                    "repair_id": repair.id,
                    "product_id": self.component.id,
                    "product_uom_qty": 5,
                    "repair_line_type": "add",
                },
                {
                    "repair_id": repair.id,
                    "product_id": self.component.id,
                    "product_uom_qty": 3,
                    "repair_line_type": "remove",
                },
            ]
        )

        self.lot.generate_component_history()

        history = self.ComponentHistory.search([("lot_id", "=", self.lot.id)])
        self.assertEqual(len(history), 3, "Should create add, remove, and adjusted add")

        remaining = history.filtered(
            lambda h: not h.invisible and h.change_type in ["add", "manufactured"]
        )
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining.qty_changed, 2.0, "Remaining quantity should be 2")

    def test_visible_component_filtering(self):
        """Test toggle and compute logic for visible_component_history_ids."""

        self.ComponentHistory.create(
            {
                "lot_id": self.lot.id,
                "product_id": self.component.id,
                "qty_changed": 1,
                "change_type": "add",
                "source_id": "repair.order,1",
                "invisible": False,
                "date": datetime.now(),
            }
        )

        self.ComponentHistory.create(
            {
                "lot_id": self.lot.id,
                "product_id": self.component.id,
                "qty_changed": 1,
                "change_type": "remove",
                "source_id": "repair.order,2",
                "invisible": True,
                "date": datetime.now(),
            }
        )

        self.lot._compute_visible_component_history_ids()
        self.assertEqual(len(self.lot.visible_component_history_ids), 2)

        self.lot.show_invisible = False
        self.lot._compute_visible_component_history_ids()
        self.assertEqual(len(self.lot.visible_component_history_ids), 1)

    def test_name_get_format(self):
        """Test name_get format for display purposes."""

        record = self.ComponentHistory.create(
            {
                "lot_id": self.lot.id,
                "product_id": self.component.id,
                "qty_changed": 1,
                "change_type": "add",
                "source_id": "repair.order,1",
                "date": datetime.now(),
            }
        )

        name = record.name_get()[0][1]
        self.assertIn("Component X", name)
        self.assertIn("add", name)

    def test_manufacturing_creates_component_history(self):
        """Test that marking MO done creates 'manufactured' component history."""

        # Create BOM
        bom = self.BoM.create(
            {
                "product_tmpl_id": self.main_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component.id,
                            "product_qty": 1.0,
                            "product_uom_id": self.UoM.id,
                        },
                    )
                ],
            }
        )

        # Create MO
        mo = self.Manufacturing.create(
            {
                "product_id": self.main_product.id,
                "product_qty": 1,
                "product_uom_id": self.UoM.id,
                "bom_id": bom.id,
                "lot_producing_id": self.lot.id,
            }
        )

        # Mark components as consumed and set output lot
        raw_move = mo.move_raw_ids[0]
        raw_move.quantity = 1
        raw_move.quantity_done = 1
        raw_move.write(
            {
                "state": "done",
                "lot_ids": [(6, 0, [])],
            }
        )

        finished_move = mo.move_finished_ids[0]
        finished_move.write(
            {"move_line_ids": [(0, 0, {"lot_id": self.lot.id, "qty_done": 1})]}
        )

        # Mark MO done (triggers component history creation)
        mo.button_mark_done()

        history = self.ComponentHistory.search(
            [
                ("lot_id", "=", self.lot.id),
                ("change_type", "=", "manufactured"),
            ]
        )
        self.assertEqual(len(history), 1)
        self.assertEqual(history.product_id, self.component)
        self.assertEqual(history.lot_id, self.lot)
