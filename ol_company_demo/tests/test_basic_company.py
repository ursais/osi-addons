# Import Python libs
import logging

# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError, MissingError

from .setup import CompanyDemoTest

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class CompanyBasicTest(CompanyDemoTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_setup(self):
        self.assertTrue(
            self.user_a.company_id == self.company_a, "User A not in correct company"
        )
        self.assertTrue(
            self.user_b.company_id == self.company_b, "User B not in correct company"
        )

        self.assertTrue(
            self.demo_group in self.user_a.groups_id.ids, "User A not in user group"
        )

        self.author_a.publisher_id = self.publisher_a
        self.book_a.author_1 = self.author_a
        self.assertTrue(
            self.book_a.author_1 == self.author_a, "Book A author not set correctly"
        )

        self.assertTrue(
            self.book_a.computed_publisher_1 == self.publisher_a,
            "Book A computed publisher 1 not set correctly",
        )

    def test_user_company_ids(self):
        """
        Basic test to check if user has access to the companies in company_ids
        """
        context = self.env.context.copy()
        context["some_value"] = "test"
        self.env.context = context
        # TODO: Expand on this

        # User A only has Company A in company_ids. It should not access Company B
        self.env = self.env(user=self.user_a)

        self.assertEqual(
            self.env["res.company"].browse(self.company_a.id).name,
            "Company A",
            "User A should be able to read from Company A",
        )
        with self.assertRaises(
            AccessError,
            msg="User A should not be able to read from Company B",
        ):
            self.env["res.company"].browse(self.company_b.id).name

        # User B only has Company B in company_ids. It should not access Company A
        self.env = self.env(user=self.user_b)
        self.assertEqual(
            self.env["res.company"].browse(self.company_b.id).name,
            "Company B",
            "User B should be able to read from Company B",
        )
        with self.assertRaises(
            AccessError,
            msg="User B should not be able to read from Company B",
        ):
            self.env["res.company"].browse(self.company_a.id).name

        # User C has Company A and B in company_ids, it should access both companies
        self.env = self.env(user=self.user_c)
        self.assertEqual(
            self.env["res.company"].browse(self.company_a.id).name,
            "Company A",
            "User C should be able to read from Company A",
        )
        self.assertEqual(
            self.env["res.company"].browse(self.company_b.id).name,
            "Company B",
            "User C should be able to read from Company B",
        )

    def test_access_basic(self):
        """
        Basic showcase of access rights
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

        # Even though book B is in company B, Odoo doesn't enforce an access right check when
        # fetching records using browse
        book_b = self.env["book"].browse(self.book_b.id)

        # That's because browse doesn't actually check that the record exists
        mystery_book = self.env["book"].browse(999999)
        with self.assertRaises(MissingError, msg="Book 999999 should not exist"):
            mystery_book.name

        # That comes when actually attempting to access values on the record
        with self.assertRaises(
            AccessError, msg="User A should not be able to read Book B"
        ):
            self.assertEqual(book_b.name, "Book B")

        # This is not the case when using search, access rights are enforced
        book_b = self.env["book"].search([("id", "=", self.book_b.id)])
        self.assertFalse(
            book_b, "User A should not be able to read Book B while searching"
        )

        # We can remove the record rule, and then access the record
        # This proves the impact of the record rules
        self.env.ref("ol_company_demo.book_record_rule").sudo().unlink()

        with self.assertRaises(ValueError, msg="Record rule should be missing"):
            self.env.ref("ol_company_demo.book_record_rule")

        book_b = self.env["book"].search([("id", "=", self.book_b.id)])
        self.assertTrue(book_b, "User A SHOULD be able to read Book B while searching")

    def test_access_to_all_companies(self):
        """
        User C has access to both companies but should only be able to access records in
        the company it's currently in
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

        # User C should be able to read Book C, as Book C has no company
        self.assertEqual(
            self.env["book"].browse(self.book_c.id).name,
            "Book C",
            "User C should be able to read book C",
        )

        self.assertEqual(
            self.env["book"].with_company(self.company_b).browse(self.book_b.id).name,
            "Book B",
            "User C should be able to read book B",
        )

    def test_check_company(self):
        """
        There is a "publisher_id" field on both the Book and Author model.
        Both have check_company=True defined on the publisher_id field.

        However, only the book model has _check_company_auto = True
        """
        self.author_a.publisher_id = self.publisher_a
        self.book_a.publisher_id = self.publisher_a

        # Confirm publisher_id is set correctly
        self.assertTrue(
            self.author_a.publisher_id == self.publisher_a,
            "Author A publisher_id was not set correctly",
        )
        self.assertTrue(
            self.book_a.publisher_id == self.publisher_a,
            "Author A publisher_id was not set correctly",
        )

        # The author model does not have _check_company_auto set to True,
        # so it will allow setting a publisher from a different company
        self.author_a.publisher_id = self.publisher_b

        # Try to set company_b on book (should fail due to _check_company_auto=True)
        with self.assertRaises(
            UserError,
            msg="Trying to set a publisher from a different company should fail",
        ):
            self.book_a.publisher_id = self.publisher_b

        # Check_company doesn't block a record with no company set
        self.book_a.publisher_id = self.publisher_c
        self.assertEqual(
            self.book_a.publisher_id,
            self.publisher_c,
            "Book A publisher_id should be Publisher C",
        )

        # Sudo won't change this behavior
        with self.assertRaises(
            UserError,
            msg="Trying to set a publisher from a different company should fail, even with sudo",
        ):
            self.book_a.sudo().publisher_id = self.publisher_b.sudo()
