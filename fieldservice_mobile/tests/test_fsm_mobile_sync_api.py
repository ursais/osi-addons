# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import fields
from odoo.addons.fieldservice.tests.test_fsm_common import FSMCommon
from odoo.exceptions import AccessError, UserError, ValidationError

TEST_IMAGE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACklEQVR4nGP4DwABAQEA"
    "GN2N9wAAAABJRU5ErkJggg=="
)


class TestFSMMobileSyncAPI(FSMCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Order = cls.env["fsm.order"]
        cls.order_stage = cls.env["fsm.stage"].create(
            {
                "name": "Mobile Sync Stage",
                "sequence": 25,
                "stage_type": "order",
                "is_display_in_mobile": True,
                "is_display_in_odoo": True,
            }
        )
        cls.clock_stage = cls.env["fsm.stage"].create(
            {
                "name": "Started Sync",
                "sequence": 6,
                "stage_type": "order",
                "is_display_in_mobile": True,
            }
        )
        cls.worker_user = cls.env["res.users"].create(
            {
                "name": "FSM Mobile Worker",
                "login": "fsm_mobile_worker_sync",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )
        cls.worker_person = cls.env["fsm.person"].create(
            {
                "name": "FSM Mobile Worker Person",
                "partner_id": cls.worker_user.partner_id.id,
            }
        )
        cls.other_person = cls.env["fsm.person"].create({"name": "Other Worker"})
        cls.assigned_order = cls.Order.create(
            {
                "location_id": cls.test_location.id,
                "stage_id": cls.order_stage.id,
                "person_id": cls.worker_person.id,
                "description": "Before sync",
            }
        )
        cls.foreign_order = cls.Order.create(
            {
                "location_id": cls.test_location.id,
                "stage_id": cls.order_stage.id,
                "person_id": cls.other_person.id,
            }
        )

    def test_sync_batch_order_clocks_signature(self):
        start = datetime.now() - timedelta(hours=1)
        Order = self.Order.with_user(self.worker_user)
        result = Order.fsm_mobile_sync_batch(
            order_id=self.assigned_order.id,
            order={
                "stage_id": self.clock_stage.id,
                "description": "After sync",
                "resolution": "Fixed",
                "person_id": self.other_person.id,  # not whitelisted
            },
            clocks=[
                {
                    "stage_id": self.clock_stage.id,
                    "start_datetime": start,
                    "duration": 1.0,
                    "total_duration": 1.0,
                }
            ],
            signature={
                "signed_by": "Customer",
                "signature": TEST_IMAGE_BASE64,
            },
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["results"]), 1)
        self.assigned_order.invalidate_recordset()
        self.assertEqual(self.assigned_order.description, "After sync")
        self.assertEqual(self.assigned_order.resolution, "Fixed")
        self.assertEqual(self.assigned_order.person_id, self.worker_person)
        self.assertEqual(self.assigned_order.signed_by, "Customer")
        self.assertTrue(self.assigned_order.signed_on)
        self.assertEqual(len(self.assigned_order.fsm_stage_history_ids), 1)
        self.assertEqual(
            result["results"][0]["clock_ids"],
            [self.assigned_order.fsm_stage_history_ids.id],
        )

    def test_sync_batch_mutations_list(self):
        second = self.Order.create(
            {
                "location_id": self.test_location.id,
                "stage_id": self.order_stage.id,
                "person_id": self.worker_person.id,
            }
        )
        result = self.Order.with_user(self.worker_user).fsm_mobile_sync_batch(
            mutations=[
                {
                    "order_id": self.assigned_order.id,
                    "order": {"resolution": "One"},
                },
                {
                    "order_id": second.id,
                    "order": {"resolution": "Two"},
                },
            ]
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(self.assigned_order.resolution, "One")
        self.assertEqual(second.resolution, "Two")

    def test_sync_rejects_unassigned_order(self):
        with self.assertRaises(AccessError):
            self.Order.with_user(self.worker_user).fsm_mobile_sync_batch(
                order_id=self.foreign_order.id,
                order={"resolution": "Nope"},
            )

    def test_sync_rejects_user_without_person(self):
        lonely = self.env["res.users"].create(
            {
                "name": "No Person User",
                "login": "fsm_mobile_no_person",
                "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.Order.with_user(lonely).fsm_mobile_sync_batch(
                order_id=self.assigned_order.id,
                order={"resolution": "Nope"},
            )

    def test_sync_missing_order_id(self):
        with self.assertRaises(ValidationError):
            self.Order.fsm_mobile_sync_batch(order={"resolution": "x"})

    def test_sync_unknown_order(self):
        with self.assertRaises(UserError):
            self.Order.with_user(self.worker_user).fsm_mobile_sync_batch(
                order_id=999999999,
                order={"resolution": "x"},
            )

    def test_sync_invalid_clock(self):
        with self.assertRaises(ValidationError):
            self.Order.with_user(self.worker_user).fsm_mobile_sync_batch(
                order_id=self.assigned_order.id,
                clocks=[{"duration": 1.0}],
            )

    def test_sync_update_existing_clock(self):
        history = self.env["fsm.stage.history"].create(
            {
                "order_id": self.assigned_order.id,
                "stage_id": self.clock_stage.id,
                "start_datetime": datetime.now() - timedelta(hours=2),
                "duration": 0.5,
                "total_duration": 0.5,
            }
        )
        new_start = datetime.now() - timedelta(hours=1)
        self.Order.with_user(self.worker_user).fsm_mobile_sync_batch(
            order_id=self.assigned_order.id,
            clocks=[
                {
                    "id": history.id,
                    "stage_id": self.clock_stage.id,
                    "start_datetime": new_start,
                    "duration": 1.5,
                    "total_duration": 1.5,
                }
            ],
        )
        history.invalidate_recordset()
        self.assertEqual(history.duration, 1.5)

    def test_pull_delta_filters_by_person_and_write_date(self):
        older = self.Order.create(
            {
                "location_id": self.test_location.id,
                "stage_id": self.order_stage.id,
                "person_id": self.worker_person.id,
                "description": "old",
            }
        )
        # Force an older write_date watermark for the first assigned order.
        past = datetime.now() - timedelta(days=2)
        self.env.cr.execute(
            "UPDATE fsm_order SET write_date = %s WHERE id = %s",
            [past, older.id],
        )
        self.assigned_order.write({"description": "fresh"})
        since = fields.Datetime.to_string(past + timedelta(days=1))
        result = self.Order.with_user(self.worker_user).fsm_mobile_pull_delta(
            since=since,
            fields=["id", "name", "description", "person_id", "write_date"],
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["person_id"], self.worker_person.id)
        pulled_ids = {rec["id"] for rec in result["records"]}
        self.assertIn(self.assigned_order.id, pulled_ids)
        self.assertNotIn(older.id, pulled_ids)
        self.assertNotIn(self.foreign_order.id, pulled_ids)

    def test_pull_includes_person_ids_worker(self):
        multi = self.Order.create(
            {
                "location_id": self.test_location.id,
                "stage_id": self.order_stage.id,
                "person_id": self.other_person.id,
                "person_ids": [(6, 0, [self.worker_person.id])],
            }
        )
        result = self.Order.with_user(self.worker_user).fsm_mobile_pull_delta(
            fields=["id", "person_id", "person_ids"]
        )
        pulled_ids = {rec["id"] for rec in result["records"]}
        self.assertIn(multi.id, pulled_ids)

    def test_create_photo_attachment(self):
        result = self.Order.with_user(
            self.worker_user
        ).fsm_mobile_create_photo_attachment(
            order_id=self.assigned_order.id,
            name="site.jpg",
            raw_bytes=b"fake-jpeg-bytes",
            mimetype="image/jpeg",
        )
        self.assertTrue(result["ok"])
        attachment = self.env["ir.attachment"].browse(result["attachment_id"])
        self.assertEqual(attachment.res_model, "fsm.order")
        self.assertEqual(attachment.res_id, self.assigned_order.id)
        self.assertEqual(attachment.name, "site.jpg")
        self.assertEqual(attachment.mimetype, "image/jpeg")

    def test_create_photo_rejects_foreign_order(self):
        with self.assertRaises(AccessError):
            self.Order.with_user(self.worker_user).fsm_mobile_create_photo_attachment(
                order_id=self.foreign_order.id,
                name="nope.jpg",
                raw_bytes=b"x",
            )
