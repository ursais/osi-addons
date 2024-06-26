# Copyright 2020 Sergio Teruel <sergio.teruel@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pass
