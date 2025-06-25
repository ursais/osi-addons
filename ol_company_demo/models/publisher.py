from odoo import models, fields, api


class Publisher(models.Model):
    _name = "publisher"
    _description = "Publisher"

    # COLUMNS #####

    name = fields.Char(string="Name", required=True)

    author_ids = fields.One2many("author", "publisher_id", string="Authors")
    book_ids = fields.One2many("book", "publisher_id", string="Books")
    company_id = fields.Many2one("res.company", string="Company")
    parent_publisher_id = fields.Many2one("publisher", string="Parent Publisher")
    top_level_publisher_id = fields.Many2one(
        "publisher",
        string="Top Level Publisher",
        compute="_compute_top_level_publisher",
    )

    # END #########

    # METHODS #####

    def _compute_top_level_publisher(self):
        """
        Mocks Odoo's "commercial_partner_id" field.
        """
        for publisher in self:
            if not publisher.parent_publisher_id:
                publisher.top_level_publisher_id = publisher
            else:
                publisher.top_level_publisher_id = (
                    publisher.parent_publisher_id.top_level_publisher_id
                )

    # END #########
