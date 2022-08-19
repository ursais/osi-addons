# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import helper
from locust import task


class StockTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(StockTaskSet, self).on_start(*args, **kwargs)
        self.Task = self.client.env["project.task"]

    @task(10)
    def edit_delivery_lines(self):
        # confirms moves in DO to finish SO
        delivery_id = helper.find_random_delivery(self.client)
        if not delivery_id:
            logging.INFO("Failed to finish DO -- none found")
            return ()
        delivery_id.action_assign()
        if all(move.state == "assigned" for move in delivery_id.move_lines):
            for operation in delivery_id.pack_operation_product_ids:
                qty_to_do = operation.product_qty
                operation.write({"qty_done": qty_to_do})
            logging.INFO("Confirmed DO: " + delivery_id.name)
            return delivery_id.do_new_transfer()

    @task(5)
    def print_picking_wave(self):
        self.Task.action_picking_wave()
        picking_wave_id = helper.find_random_picking_wave(self.client)
        if not picking_wave_id:
            logging.INFO("Failed to print Picking Wave -- none found")
            return ()
        return picking_wave_id.print_picking()

    @task(5)
    def confirm_picking_wave(self):
        picking_wave_id = helper.find_random_picking_wave_running(self.client)
        if not picking_wave_id:
            logging.INFO("Failed to confirm Picking Wave --none found")
            return ()
        return picking_wave_id.done()
