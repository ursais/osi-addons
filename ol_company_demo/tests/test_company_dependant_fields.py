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

    def test_company_dependant_field_with_user(self):
        """
        Basic read/write tests for company_dependent fields

        Writing a company_dependent field should only have that value read in the context of the company it was written in
        """
        # User A only has Company A in company_ids. It should not access Company B
        user_a_ctx = self.env(user=self.user_a)
        user_b_ctx = self.env(user=self.user_b)
        self.assertEqual(
            user_a_ctx["res.company"].browse(self.company_a.id).name,
            "Company A",
            "User A should be able to read from Company A",
        )
        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read from Company B",
        ):
            user_a_ctx["res.company"].browse(self.company_b.id).name

        # Write to book a in the context of Company A
        author_c = user_a_ctx["author"].browse(self.author_c.id)
        author_c.write({"company_dependent_string": "Test A"})

        self.assertEqual(
            author_c.company_dependent_string,
            "Test A",
            "We should receive the value we wrote in the present company",
        )

        self.assertEqual(
            user_a_ctx["author"].browse(self.author_c.id).company_dependent_string,
            "Test A",
            "We should receive the value we wrote in the present company",
        )

        self.assertNotEqual(
            user_b_ctx["author"].browse(self.author_c.id).company_dependent_string,
            "Test A",
            "We should not receive the value we wrote in another company",
        )

    def test_company_dependant_field_with_company(self):
        """
        Testing with_company for reading company_dependent fields
        """
        user_a_ctx = self.env(user=self.user_a)
        user_b_ctx = self.env(user=self.user_b)

        # Write to book a in the context of Company A
        author_c_as_user_a = user_a_ctx["author"].browse(self.author_c.id)
        author_c_as_user_a.write({"company_dependent_string": "Test A"})

        self.assertEqual(
            author_c_as_user_a.company_dependent_string,
            "Test A",
            "We should receive the value we wrote in the present company",
        )

        # Write to book a in the context of Company B
        author_c_as_user_b = user_b_ctx["author"].browse(self.author_c.id)

        self.assertFalse(
            author_c_as_user_b.company_dependent_string,
            "We should not receive a value while in company B context",
        )

        author_c_as_user_b.write({"company_dependent_string": "Test B"})

        self.assertEqual(
            author_c_as_user_b.company_dependent_string,
            "Test B",
            "We should receive the value we wrote in the present company",
        )

        author_c = self.env["author"].browse(self.author_c.id)

        self.assertEqual(
            author_c.with_company(self.company_a.id).company_dependent_string,
            "Test A",
            "We should receive the value we wrote in Company A",
        )

        self.assertEqual(
            author_c.with_company(self.company_b.id).company_dependent_string,
            "Test B",
            "We should receive the value we wrote in Company B",
        )

    def test_computed_caching(self):
        """
        With the following function on the author model, we should find that all_books_filtered
        always matches the company of the author record

        def _compute_books_filtered(self):
            for author in self:
                author.all_books_filtered = author.all_books.filtered(
                    lambda b: b.company_id == author.company_id
                )[0]

        This value will need to be cleared from cache when we change the company_id of the book
        """
        self.assertEqual(
            self.author_a.all_books_filtered,
            self.book_a,
            "The filtered book should match the company of the author",
        )
        self.assertEqual(
            self.author_b.all_books_filtered,
            self.book_b,
            "The filtered book should match the company of the author",
        )

        # Applies for when the company is not set
        self.assertEqual(
            self.author_c.all_books_filtered,
            self.book_c,
            "The filtered book should match the company of the author",
        )

        self.book_c.write({"company_id": self.company_b.id})

        self.assertEqual(
            self.author_c.all_books_filtered,
            self.book_c,
            "The filtered book should still be in the cache",
        )

        # Clear from the cache
        self.author_c.invalidate_recordset(fnames=["all_books_filtered"])

        self.assertFalse(
            self.author_c.all_books_filtered,
            "Author C should not have an all_book_filtered value as no books have company_id unset",
        )

    def test_loop_through_companies_with_user(self):
        """
        You can use with_user for company specific values
        """
        self.env(user=self.user_a)["author"].browse(self.author_c.id).write(
            {"company_dependent_string": "Test A"}
        )
        self.env(user=self.user_b)["author"].browse(self.author_c.id).write(
            {"company_dependent_string": "Test B"}
        )

        # Switch to user A and prove you can't read from both
        self.env = self.env(user=self.user_a)
        author_c = self.env["author"].browse(self.author_c.id)
        self.assertEqual(
            author_c.company_dependent_string,
            "Test A",
            "User A should be able to read from Company A",
        )
        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read from Company B",
        ):
            author_c.with_company(self.company_b.id).company_dependent_string

        author_c = author_c.with_user(self.user_b)
        self.assertEqual(
            author_c.company_dependent_string,
            "Test B",
            "We should be able to read from Company B with user B",
        )
