# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import helper
from locust import task


class ProjectTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(ProjectTaskSet, self).on_start(*args, **kwargs)

    @task(10)
    def edit_task(self):
        task_id = helper.find_random_task(self.client)
        if not task_id:
            logging.INFO("Failed to edit Task -- none found")
            return ()
        user_id = helper.find_associated_user(self.client, task_id.site_id)
        if not user_id:
            logging.INFO("Failed to edit Task -- none found")
            return ()
        stage_id = self.client.env["project.task.type"].search_read(
            [("name", "=", "Reviewed")], ["id"]
        )[0]["id"]
        vals = {
            "user_id": user_id.id,
            "date_start": "2020-01-01 00:00:00",
            "planned_hours": 40,
            "stage_id": stage_id,
        }
        return task_id.write(vals)

    @task(10)
    def confirm_task(self):
        task_id = helper.find_random_task_ready(self.client)
        if not task_id:
            logging.INFO("Failed to confirm Task -- none found")
            return ()
        stage_id = self.client.env["project.task.type"].search_read(
            [("name", "=", "Work Done")], ["id"]
        )[0]["id"]
        task_id.write({"stage_id": stage_id})
        return task_id
