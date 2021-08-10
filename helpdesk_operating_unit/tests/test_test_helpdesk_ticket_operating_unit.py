# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo.tests import common


class TestHelpdeskTicketOperatingUnit(common.TransactionCase):
    def setUp(self):
        super(TestHelpdeskTicketOperatingUnit, self).setUp()
        self.helpdesk_obj = self.env["helpdesk.ticket"]
        self.res_users_model = self.env["res.users"]

        # Groups
        self.grp_manager = self.env.ref("helpdesk.group_helpdesk_manager")
        self.grp_user = self.env.ref("helpdesk.group_helpdesk_user")
        # Company
        self.company = self.env.ref("base.main_company")
        # Main Operating Unit
        self.main_OU = self.env.ref("operating_unit.main_operating_unit")
        # B2C Operating Unit
        self.b2c_OU = self.env.ref("operating_unit.b2c_operating_unit")
        # Create User 1 with Main OU
        self.user1 = self._create_user(
            "user_1", [self.grp_user, self.grp_manager], self.company, [self.main_OU]
        )
        # Create User 2 with B2C OU
        self.user2 = self._create_user(
            "user_2", [self.grp_user, self.grp_manager], self.company, [self.b2c_OU]
        )

        self.helpdesk_ticket1 = self._create_helpdesk_ticket(
            self.user1.id, self.main_OU
        )
        self.helpdesk_ticket2 = self._create_helpdesk_ticket(self.user2.id, self.b2c_OU)

    def _create_user(self, login, groups, company, operating_units):
        """ Create a user. """
        group_ids = [group.id for group in groups]
        user = self.res_users_model.create(
            {
                "name": login,
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "operating_unit_ids": [(4, ou.id) for ou in operating_units],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    def _create_helpdesk_ticket(self, uid, operating_unit):
        helpdesk = self.helpdesk_obj.with_user(uid).create(
            {
                "name": "Demo helpdesk",
                "operating_unit_id": operating_unit.id,
            }
        )
        return helpdesk

    def test_helpdesk(self):
        # User 2 is only assigned to B2C Operating Unit, and cannot
        # access Agreement for Main Operating Unit.
        helpdesk_ticket_ids = self.helpdesk_obj.with_user(self.user2.id).search(
            [
                ("id", "=", self.helpdesk_ticket2.id),
                ("operating_unit_id", "=", self.main_OU.id),
            ]
        )
        self.assertEqual(
            helpdesk_ticket_ids.ids,
            [],
            "User 2 should not have " " access to %s" % self.main_OU.name,
        )
        self.assertEqual(self.helpdesk_ticket1.operating_unit_id.id, self.main_OU.id)
