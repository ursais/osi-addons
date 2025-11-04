from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestOLException(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.exception_rule_manager = cls.env.ref('base_exception.group_exception_rule_manager')
        cls.onlogic_internal_user = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal.user@onligic.com',
            'email': 'internal.user@onligic.com',
        })
        cls.exception_rule = cls.env["exception.rule"].create(
           {
               "name": "No ZIP code on destination",
               "sequence": 10,
               "model": "sale.order",
               "code": "if not self.partner_id.zip: failed=True",
               "exception_type": "by_py_code",
           }
        )

    def test_exception_with_internal_user(self):
        """Confirm that a non-admin user receives and exception"""
        self.onlogic_internal_user.groups_id += self.exception_rule_manager
        with self.assertRaises(UserError):
            self.exception_rule.with_user(self.onlogic_internal_user.id).copy()

        with self.assertRaises(UserError):
            self.exception_rule.with_user(self.onlogic_internal_user.id).write({
                "exception_type": "by_py_code"
            })

    def test_exception_with_admin_user(self):
        """Confirm that an admin user does not receive an exception"""
        self.onlogic_internal_user.groups_id += self.exception_rule_manager
        
        try:
            self.exception_rule.with_user(self.env.user.id).copy()
        except UserError:
            self.fail("copy() raised UserError unexpectedly!")
        
        try:
            self.exception_rule.with_user(self.env.user.id).write({
                "exception_type": "by_py_code"
            })
        except UserError:
            self.fail("write() raised UserError unexpectedly!")
        self.exception_rule._get_view()
