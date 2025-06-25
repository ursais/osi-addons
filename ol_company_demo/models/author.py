from odoo import models, fields, api


class Author(models.Model):
    _name = "author"
    _description = "Author"

    # COLUMNS #####

    name = fields.Char(string="Name", required=True)
    book_ids = fields.Many2many("book", string="Books")
    publisher_id = fields.Many2one(
        "publisher",
        string="Publishers",
        check_company=True,
    )
    company_id = fields.Many2one("res.company", string="Company")

    company_dependent_string = fields.Char(
        string="Company Dependent String",
        required=True,
        company_dependent=True,
    )

    all_books = fields.Many2many(
        "book",
        string="All Books",
        compute="_compute_books",
    )
    all_books_filtered = fields.Many2one(
        "book",
        string="All Books",
        compute="_compute_books_filtered",
    )

    # END #########

    # METHODS #####

    def _compute_books(self):
        for author in self:
            author.all_books = author.env["book"].search([])

    def _compute_books_filtered(self):
        for author in self:
            all_books_filtered = author.all_books.filtered(
                lambda b: b.company_id == author.company_id
            )
            author.all_books_filtered = (
                all_books_filtered[0] if all_books_filtered else None
            )

    # END #########
