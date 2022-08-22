from odoo import models, fields


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library book'

    # sorts the books from oldest
    _order = 'date_release desc, name'

    # to use the shortname field as the record representation
    _rec_name = 'short_name'
    short_name = fields.Char('Short Title', required=True)

    state = fields.Selection(
        [('draft', 'Not Available'),
         ('available', 'Available'),
         ('lost', 'Lost')],
        'State')
    description = fields.Html('Description')
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages')
    cost_price = fields.Float(
        'Book Cost', digits='Book Price')
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  # Optional precision decimals,
    )

    name = fields.Char('Title', required=True)
    author_ids = fields.Many2many(
        'res,partner',
        string='Authors'
    )
