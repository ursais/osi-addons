from odoo import models, fields, api


class Book(models.Model):
    _name = "book"
    _description = "Book"
    _check_company_auto = True

    # COLUMNS #####

    name = fields.Char(string="Title", required=True)
    pages = fields.Integer(string="Pages")
    author_1 = fields.Many2one("author", string="Authors")
    author_2 = fields.Many2one("author", string="Authors")
    author_3 = fields.Many2one("author", string="Authors")
    publisher_id = fields.Many2one(
        "publisher",
        string="Publisher",
        check_company=True,
    )
    company_id = fields.Many2one("res.company", string="Company")

    computed_publisher_1 = fields.Many2one(
        "publisher",
        string="Computed Publisher 1",
        compute="_compute_publisher_1",
    )
    computed_publisher_2 = fields.Many2one(
        "publisher",
        string="Computed Publisher 2",
        compute="_compute_publisher_2",
        check_company=True,
    )
    computed_publisher_3 = fields.Many2one(
        "publisher",
        string="Computed Publisher 3",
        compute="_compute_publisher_3",
        check_company=True,
    )

    force_company_string = fields.Char(
        string="Force Company String",
        compute="_compute_force_company_string",
    )

    # END #########

    # METHODS #####

    @api.depends("author_1", "author_1.publisher_id")
    def _compute_publisher_1(self):
        for book in self:
            book.computed_publisher_1 = book.author_1.publisher_id or None

    @api.depends("author_2", "author_2.publisher_id")
    def _compute_publisher_2(self):
        for book in self:
            book.computed_publisher_2 = book.author_2.publisher_id or None

    @api.depends("author_3", "author_3.publisher_id")
    def _compute_publisher_3(self):
        for book in self:
            book.computed_publisher_3 = book.author_3.publisher_id or None

    @api.depends_context("force_company")
    def _compute_force_company_string(self):
        for book in self:
            try:
                company_id = (
                    self.env.context.get("force_company") or record.company_id.id
                )
                book.force_company_string = company_id.name
            except:
                book.force_company_string = "Can't access company"

    # END #########
