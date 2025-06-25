# Import Python libs
import logging

# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError

from .setup import CompanyDemoTest

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class CompanyDependantTest(CompanyDemoTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_force_company(self):
        """
        Test that force_company works as expected

        WARNING odoo.models: Context key 'force_company' is no longer supported. Use with_company(company) instead.
        """
        # TODO: Why?
        self.assertEqual(
            self.book_a.force_company_string,
            "Can't access company",
            "Can't access company without force_company",
        )

        self.assertEqual(
            self.book_a.with_context(force_company=self.company_a).force_company_string,
            "Company A",
            "Company A should be returned with force_company",
        )

        self.assertEqual(
            self.book_a.with_context(force_company=self.company_b).force_company_string,
            "Company B",
            "Company B should be returned with force_company",
        )
