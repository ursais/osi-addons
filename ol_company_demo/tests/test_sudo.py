# Import Python libs
import logging

# Import Odoo libs

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, UserError

from .setup import CompanyDemoTest

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class CompanySudoTest(CompanyDemoTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Start with user_a for all tests
        cls.env = cls.env(user=cls.user_a)

    def test_user_access_with_sudo(self):
        """
        Test how using sudo interacts with company restrictions while not using a superuser
        """

        # Switch to user_a and check access
        self.env = self.env(user=self.user_a)
        self.assertEqual(
            self.env["res.company"].browse(self.company_a.id).name, "Company A"
        )

        # You can't call sudo on the whole environment outright
        with self.assertRaises(AttributeError, msg="You can't call sudo on the env"):
            self.env.sudo()

        # Two distinct models, one with sudo and one without
        book_model = self.env["book"]
        book_model_with_sudo = self.env["book"].sudo()

        self.assertFalse(book_model.env.su)
        self.assertTrue(book_model_with_sudo.env.su)

        # The current context isn't sudo
        self.assertFalse(self.env.su)

        # Assert the current user is A
        self.assertEqual(book_model.browse(self.book_a.id).name, "Book A")

        self.assertEqual(book_model_with_sudo.browse(self.book_a.id).name, "Book A")

        # User A can read Book B via the sudo recordset only
        self.assertEqual(book_model_with_sudo.browse(self.book_b.id).name, "Book B")

        with self.assertRaises(
            AccessError, msg="User A should not be able to read Book B"
        ):
            self.assertEqual(book_model.browse(self.book_b.id).name, "Book B")

        # Confirm sudo access on separate environments is unchanged
        self.assertFalse(book_model.env.su)
        self.assertTrue(book_model_with_sudo.env.su)
        self.assertFalse(self.env.su)

    def test_admin_user(self):
        """
        If we switch to the admin user, the environment should not be sudo
        """
        self.assertFalse(self.env.su, "Env should not be sudo")

        admin_user = self.env.ref("base.user_admin")
        self.assertEqual(admin_user.login, "admin", "Admin user should be admin")

        self.assertFalse(self.env.su, "Env should not be sudo")

        self.env = self.env(user=admin_user)

        self.assertEqual(self.env.user.login, "admin", "Env should not be sudo")
        self.assertFalse(
            self.env.su, "Env should not be sudo even if the user is the admin user"
        )

    def test_root_user(self):
        """
        If we switch to the root user, the environment should be sudo

        NOTE: We should never do this
        """
        self.assertFalse(self.env.su, "Env should not be sudo")

        root_user = self.env.ref("base.user_root")

        self.assertEqual(root_user.login, "__system__", "Admin user should be admin")

        self.assertFalse(self.env.su, "Env should not be sudo")

        self.env = self.env(user=root_user)

        self.assertEqual(self.env.user.login, "__system__", "Env should not be sudo")
        self.assertTrue(
            self.env.su, "Env should be sudo now that the user is the root user"
        )

    def test_retrieving_records_with_su(self):
        """
        Reading records as a superuser does not automatically make the recordset sudo
        """
        self.assertFalse(self.env.su, "Env should not be sudo")
        res = self.env["book"].browse(self.book_a.id)
        self.assertFalse(
            res.env.su, "Returned record should not be in a sudo environment"
        )

        # Switch to the system user
        root_user = self.env.ref("base.user_root")
        self.env = self.env(user=root_user)

        # Note that the recordset is now sudo
        res = self.env["book"].browse(self.book_a.id)
        self.assertEqual(res.name, "Book A", "Admin user should be able to read Book A")

        self.assertTrue(res.env.su, "Book A should be in a sudo environment")

        # Leave sudo env
        self.env = self.env(user=self.user_a)
        self.assertFalse(self.env.su, "Env should not be sudo")

        res = self.env["book"].browse(self.book_a.id)
        self.assertFalse(
            res.env.su, "Returned record should not be in a sudo environment"
        )

        # Calling sudo makes this recordset sudo
        res = self.env["book"].sudo().browse(self.book_a.id)
        self.assertTrue(
            res.env.su, "Book A should be in a sudo environment if sudo() is used"
        )

    def test_sudo_record_swap(self):
        """
        Test if sudo recordsets swap correctly
        """

        book_model = self.env["book"].browse(self.book_a.id)
        self.assertEqual(
            self.env["res.company"].browse(self.company_a.id).name, "Company A"
        )

        # Recordset is not sudo
        self.assertFalse(
            book_model.env.su, "Book A should not be in a sudo environment"
        )

        self.assertEqual(book_model.name, "Book A", "Book A should be accessible")

        book_model = book_model.sudo()

        # Recordset is now sudo
        self.assertTrue(book_model.env.su, "Book A should be in a sudo environment")

        self.assertEqual(book_model.name, "Book A", "Book A should be accessible")

        book_model = book_model.with_user(self.user_a)

        # Recordset is not sudo
        self.assertFalse(
            book_model.env.su, "Book A should not be in a sudo environment"
        )

        self.assertEqual(book_model.name, "Book A", "Book A should be accessible")

    def test_search(self):
        """
        There are two ways to retrieve all of the records in any company given current record rules
        """
        # User C has access to both companies
        self.env = self.env(user=self.user_c)

        # First, note that we can retrieve both companies as user C without sudo
        companies = self.env["res.company"].search([])
        self.assertEqual(len(companies), 2, "There should be two companies found")
        self.assertFalse(
            companies.env.su, "Companies should not be in a sudo environment"
        )

        books = self.env["book"].with_context(active_test=False).search([])

        # User C should find the book in it's current company (A) and the one with no company (book c)
        self.assertTrue(len(books) == 2, "There should be two books found")

        books_sudo = self.env["book"].sudo().with_context(active_test=False).search([])

        # Using Sudo, all books should be found
        self.assertTrue(len(books_sudo) == 3, "There should be three books found")

        # However, the environment is sudo, which can cause problems if we maintain this environment
        # and use it for actions in the future
        self.assertTrue(books_sudo.env.su, "books_sudo environment should be sudo")
        self.assertFalse(
            books.env.su, "The regular books environment should not be sudo"
        )

        # We can retieve all records without sudo by iterating over companies
        books = self.env["book"].browse([])
        for company in companies:
            self.env.user.company_id = company
            books |= self.env["book"].search([])

        self.assertTrue(len(books) == 3, "There should be three books found")
        self.assertFalse(
            books.env.su, "The regular books environment should not be sudo"
        )

        # Alternatively, we can use sudo and then ensure we leave the sudo environment
        books = self.env["book"].sudo().search([])
        self.assertTrue(len(books) == 3, "There should be three books found")
        self.assertTrue(books.env.su, "The books environment should be sudo")

        books = books.with_user(self.env.user)
        self.assertTrue(len(books) == 3, "There should be three books found")
        self.assertFalse(books.env.su, "The books environment should not be sudo")
