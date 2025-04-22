from odoo.tests.common import TransactionCase


class CompanyDemoTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

        cls.demo_group = cls.env.ref("ol_company_demo.base_group").id

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "User A",
                "login": "user_a",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "User B",
                "login": "user_b",
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, [cls.company_b.id])],
            }
        )
        cls.user_c = cls.env["res.users"].create(
            {
                "name": "User C",
                "login": "user_c",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id, cls.company_b.id])],
            }
        )

        # Add users to demo group
        cls.user_a.write(
            {"groups_id": [(4, cls.env.ref("ol_company_demo.base_group").id)]}
        )
        cls.user_b.write(
            {"groups_id": [(4, cls.env.ref("ol_company_demo.base_group").id)]}
        )
        cls.user_c.write(
            {"groups_id": [(4, cls.env.ref("ol_company_demo.base_group").id)]}
        )

        cls.publisher_a = cls.env["publisher"].create(
            {"name": "Publisher A", "company_id": cls.company_a.id}
        )
        cls.publisher_b = cls.env["publisher"].create(
            {"name": "Publisher B", "company_id": cls.company_b.id}
        )
        cls.publisher_c = cls.env["publisher"].create(
            {"name": "Publisher C", "company_id": False}
        )

        cls.author_a = cls.env["author"].create(
            {"name": "Author A", "company_id": cls.company_a.id}
        )
        cls.author_b = cls.env["author"].create(
            {"name": "Author B", "company_id": cls.company_b.id}
        )
        cls.author_c = cls.env["author"].create(
            {"name": "Author C", "company_id": False}
        )

        cls.book_a = cls.env["book"].create(
            {
                "name": "Book A",
                "pages": 100,
                "company_id": cls.company_a.id,
            }
        )
        cls.book_b = cls.env["book"].create(
            {
                "name": "Book B",
                "pages": 200,
                "company_id": cls.company_b.id,
            }
        )
        cls.book_c = cls.env["book"].create(
            {
                "name": "Book C",
                "pages": 300,
            }
        )
