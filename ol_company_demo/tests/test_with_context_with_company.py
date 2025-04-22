# Import Python libs
import logging

# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError

from .setup import CompanyDemoTest

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class CompanyContextTest(CompanyDemoTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_with_context(self):
        """
        Using with_context won't bypass access rights
        """
        self.env = self.env(user=self.user_a)
        self.assertEqual(
            self.env.company,
            self.company_a,
            "Current env company should be Company A",
        )
        self.assertEqual(
            self.env.user.company_id,
            self.company_a,
            "Current env user's company should be Company A",
        )

        # "Regular" access rights will block user A from accessing book B
        with self.assertRaises(
            AccessError, msg="User A should not be able to read Book B"
        ):
            self.assertEqual(self.env["book"].browse(self.book_b.id).name, "Book B")

        # with_context doesn't bypass this
        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read Book B, even using with_context",
        ):
            self.env["book"].with_context(company_id=self.company_b.id).browse(
                self.book_b.id
            ).name

        # with_context and a new env doesn't bypass this either
        book_model = self.env["book"].with_context(company_id=self.company_b.id)

        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read Book B, even using with_context with a new env",
        ):
            book_model.with_context(company_id=self.company_b.id).browse(
                self.book_b.id
            ).name

    def test_with_company(self):
        """
        Using with_company won't bypass access rights
        """
        self.env = self.env(user=self.user_a)
        self.assertEqual(
            self.env.company,
            self.company_a,
            "Current env company should be Company A",
        )
        self.assertEqual(
            self.env.user.company_id,
            self.company_a,
            "Current env user's company should be Company A",
        )

        # "Regular" access rights will block user A from accessing book B
        with self.assertRaises(
            AccessError, msg="User A should not be able to read Book B"
        ):
            self.assertEqual(self.env["book"].browse(self.book_b.id).name, "Book B")

        # with_company doesn't bypass this
        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read Book B, even using with_company",
        ):
            self.env["book"].with_company(self.company_b).browse(self.book_b.id).name

        # with_company and a new env doesn't bypass this either
        book_model = self.env["book"]

        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read Book B, even using with_company with a new env",
        ):
            book_model.with_company(self.company_b).browse(self.book_b.id).name

    def test_with_context_vs_with_company(self):
        """
        User C has access to both companies, can only access Book B using with_company
        """
        self.env = self.env(user=self.user_c)

        self.assertEqual(
            self.env.user.company_id, self.company_a, "User C should be in Company A"
        )

        # User C should be able to read Book A
        self.assertEqual(
            self.env["book"].browse(self.book_a.id).name,
            "Book A",
            "User C should be able to read book C",
        )

        # User C should not be able to read Book B while in company A
        with self.assertRaises(
            AccessError, msg="User C should not be able to read Book B"
        ):
            self.env["book"].browse(self.book_b.id).name

        # Blocked while using with_context
        with self.assertRaises(
            AccessError,
            msg="User C should not be able to read Book B using with_context",
        ):
            self.env["book"].with_context(company_id=self.company_b.id).browse(
                self.book_b.id
            ).name

        # Allowed while using with_company
        self.assertEqual(
            self.env["book"].with_company(self.company_b).browse(self.book_b.id).name,
            "Book B",
            "User C should be able to read book B using with_company",
        )
