# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.fieldservice.tests.test_fsm_common import FSMCommon


class TestFsmTracking(FSMCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Tracking = cls.env["fsm.tracking"]
        cls.uom_m = cls.env.ref("uom.product_uom_meter")
        cls.order_stage = cls.env["fsm.stage"].create(
            {
                "name": "Tracking Order Stage",
                "sequence": 25,
                "stage_type": "order",
                "start_tracking": True,
                "stop_tracking": False,
                "notify_customer": True,
                "notify_dispatcher": True,
                "distance_to_next_stop": True,
            }
        )
        cls.test_order = cls.env["fsm.order"].create(
            {
                "location_id": cls.test_location.id,
                "stage_id": cls.order_stage.id,
            }
        )

    def test_person_tracking_fields(self):
        self.test_person.write(
            {
                "worker_allow_tracking": True,
                "track_lat": 33.44840,
                "track_long": -112.07400,
                "loc_rad": 12.5,
                "loc_time": "2026-07-24 18:00:00",
                "rad_uom": self.uom_m.id,
                "match_rad": 100,
                "track_intv_coarse": 60,
                "fence_rad": 250,
                "route_stage": "enroute",
            }
        )
        self.assertTrue(self.test_person.worker_allow_tracking)
        self.assertAlmostEqual(self.test_person.track_lat, 33.44840, places=5)
        self.assertAlmostEqual(self.test_person.track_long, -112.07400, places=5)
        self.assertEqual(self.test_person.rad_uom, self.uom_m)
        self.assertEqual(self.test_person.route_stage, "enroute")

    def test_stage_tracking_flags(self):
        self.assertTrue(self.order_stage.start_tracking)
        self.assertFalse(self.order_stage.stop_tracking)
        self.assertTrue(self.order_stage.notify_customer)
        self.assertTrue(self.order_stage.notify_dispatcher)
        self.assertTrue(self.order_stage.distance_to_next_stop)
        self.order_stage.write(
            {
                "start_tracking": False,
                "stop_tracking": True,
            }
        )
        self.assertFalse(self.order_stage.start_tracking)
        self.assertTrue(self.order_stage.stop_tracking)

    def test_create_fsm_tracking(self):
        tracking = self.Tracking.create(
            {
                "partner_id": self.test_person.id,
                "order_id": self.test_order.id,
                "latitude": 33.45,
                "longitude": -112.07,
                "timestamp": "2026-07-24 18:05:00",
                "accuracy": 8.0,
                "route_stage": "working",
                "last_loc_age": 30,
                "substatus": "On site",
            }
        )
        self.assertEqual(tracking.partner_id, self.test_person)
        self.assertEqual(tracking.order_id, self.test_order)
        self.assertEqual(tracking.route_stage, "working")
        self.assertEqual(tracking.substatus, "On site")
        self.assertEqual(tracking.last_loc_age, 30)
