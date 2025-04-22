# Import Python libs
import logging

# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError

from .setup import CompanyDemoTest

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class CompanyComputedTest(CompanyDemoTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_basic_computed_function_value(self):
        """
        Basic proof of computed functions with respect to companies

        @api.depends("author_1")
        def _compute_publisher_1(self):
            for book in self:
                book.computed_publisher_1 = book.author_1.publisher_id or None

        computed_publisher_1 does NOT have check_company
        computed_publisher_2 does have check_company
        """
        self.env = self.env(user=self.user_a)
        self.author_a.publisher_id = self.publisher_a
        self.book_a.author_1 = self.author_a
        self.book_a.author_2 = self.author_a
        self.assertTrue(
            self.book_a.author_1 == self.author_a, "Book A author not set correctly"
        )

        self.assertTrue(
            self.book_a.computed_publisher_1 == self.publisher_a,
            "Book A computed publisher 1 not set correctly",
        )
        self.assertTrue(
            self.book_a.computed_publisher_2 == self.publisher_a,
            "Book A computed publisher 2 not set correctly",
        )

        self.assertTrue(
            self.book_a.computed_publisher_1.name == "Publisher A",
            "Book A computed publisher 1 should be accessible",
        )
        self.assertTrue(
            self.book_a.computed_publisher_2.name == "Publisher A",
            "Book A computed publisher 1 should be accessible",
        )

        """
        Book > Author > Publisher
        Switch company on the publisher, see if it affects the computed field
        on the book

        It shouldn't on computed_publisher_1 because check_company=False
        It should on computed_publisher_2 because check_company=True
        """

        # Switching the company doesn't immediately affect the computed field
        self.publisher_a.write({"company_id": self.company_b.id})
        self.assertTrue(
            self.book_a.computed_publisher_1.name == "Publisher A",
            "Book A computed publisher 1 should be accessible",
        )
        self.assertTrue(
            self.book_a.computed_publisher_2.name == "Publisher A",
            "Book A computed publisher 2 should be accessible",
        )

        # Note that this isn't related to cache
        self.book_a.invalidate_recordset(
            fnames=["computed_publisher_1", "computed_publisher_1"]
        )
        self.assertTrue(
            self.book_a.computed_publisher_1.name == "Publisher A",
            "Book A computed publisher 1 should be accessible",
        )
        self.assertTrue(
            self.book_a.computed_publisher_2.name == "Publisher A",
            "Book A computed publisher 2 should be accessible",
        )

        # Reset the publisher, trigger the recompute
        self.book_a.author_1.publisher_id = False
        self.book_a.author_2.publisher_id = False

        self.book_a._compute_publisher_1()
        self.book_a._compute_publisher_2()

        # Note the publisher is no longer set for computed_publisher_1
        self.assertFalse(
            self.book_a.computed_publisher_1.name == "Publisher A",
            "Book A computed publisher 1 should be accessible",
        )
        # computed_publisher_2 was not able to have it set due to check_company=True
        self.assertFalse(
            self.book_a.computed_publisher_2,
            "Book A computed publisher 2 should be unset",
        )

    def test_compute_publisher_check_company(self):
        """
        Test if check_company on a computed field that sets a related record
        behaves as expected.

        Note that computed fields with check_company seem to behave strangely
        """

        self.author_a.write({"publisher_id": self.publisher_a})
        self.author_b.write({"publisher_id": self.publisher_b})

        self.book_a.write({"author_3": self.author_a})
        self.book_b.write({"author_3": self.author_b})

        # Confirm computed publisher 3 is set correctly
        self.assertEqual(
            self.book_a.computed_publisher_3,
            self.publisher_a,
            "Book A computed publisher 3 should be Publisher A",
        )
        self.assertEqual(
            self.book_b.computed_publisher_3,
            self.publisher_b,
            "Book B computed publisher 3 should be Publisher B",
        )

        """
        Book > Author > Publisher
        Switch the author to one in a different company
        """

        # Change author to a different company and check
        self.book_a.write({"author_3": self.author_b})

        """
        TODO: This behavior is odd and should be investigated further

        The computed field obviously recomputes, but Odoo
        seems to not enforce the check_company=True on the computed field.

        However, when calling the compute function directly on the record, 
        it does enforce the check_company=True and throws an error
        """

        self.assertTrue(
            self.book_a.computed_publisher_3 == self.publisher_b,
            "Book A computed publisher 3 is still publisher B",
        )

        with self.assertRaises(
            UserError,
            msg="Calling the compute function raises a UserError as the publisher is from a different company",
        ):
            self.book_a._compute_publisher_3()

        # Note that this isn't related to cache
        self.book_a.invalidate_recordset(fnames=["computed_publisher_3"])
        self.assertTrue(
            self.book_a.computed_publisher_3 == self.publisher_b,
            "Book A computed publisher 3 is still publisher B",
        )
