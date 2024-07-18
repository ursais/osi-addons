from odoo.tests import TransactionCase
from odoo.exceptions import UserError


class TestOLException(TransactionCase):

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

    def test01_exception_with_internal_user(self):
        self.onlogic_internal_user.groups_id += self.exception_rule_manager
        with self.assertRaises(UserError):
            self.exception_rule.with_user(self.onlogic_internal_user.id).copy()

        with self.assertRaises(UserError):
            self.exception_rule.with_user(self.onlogic_internal_user.id).write({
                "exception_type": "by_py_code"
            })

    def test02_exception_with_admin_user(self):
        self.onlogic_internal_user.groups_id += self.exception_rule_manager
        self.exception_rule.with_user(self.env.user.id).copy()
        self.exception_rule.with_user(self.env.user.id).write({
            "exception_type": "by_py_code"
        })
        self.exception_rule._get_view()
