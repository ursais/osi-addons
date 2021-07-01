# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import HelpdeskTransactionCase


class TestHelpdeskAssign(HelpdeskTransactionCase):
    """Test used to check that the base functionalities of Helpdesk Team
    Assigned Tickets function as expected.
    - test_number_assign: tests that the assigned_tickets field
    computes properly.
    """

    def test_number_assign(self):
        # helpdesk manager creates a helpdesk team
        # (the .sudo() at the end is to avoid potential uid problems)
        self.test_team = (
            self.env["helpdesk.team"]
            .sudo(self.helpdesk_manager.id)
            .create({"name": "Test Team"})
            .sudo()
        )

        # get possible tickets from previous installs that are not assigned
        prev = self.env["helpdesk.ticket"].search_count([("user_id", "=", False)])

        # we create 10 tickets
        # make half assigned and half unassigned
        for i in range(10):
            if i % 2 == 0:
                self.env["helpdesk.ticket"].create(
                    {
                        "name": "test ticket " + str(i),
                        "team_id": self.test_team.id,
                    }
                )
            else:
                self.env["helpdesk.ticket"].create(
                    {
                        "name": "test ticket " + str(i),
                        "team_id": self.test_team.id,
                        "user_id": self.helpdesk_user.id,
                    }
                )

        # ensure we have an equal number of assigned and unassigned tickets
        self.assertEqual(
            self.env["helpdesk.ticket"].search_count([("user_id", "=", False)]) - prev,
            5,
        )
        self.assertEqual(
            self.env["helpdesk.ticket"].search_count(
                [("user_id", "=", self.helpdesk_user.id)]
            ),
            5,
        )

        # ensure fields assigned_tickets and unassigned_tickets are equal
        u_count = self.env["helpdesk.team"].browse(self.test_team.id).unassigned_tickets
        a_count = self.env["helpdesk.team"].browse(self.test_team.id).assigned_tickets

        self.assertEqual(
            self.env["helpdesk.ticket"].search_count([("user_id", "=", False)]) - prev,
            u_count,
        )
        self.assertEqual(
            self.env["helpdesk.ticket"].search_count(
                [("user_id", "=", self.helpdesk_user.id)]
            ),
            a_count,
        )
