# Import Odoo libs
from odoo import models


class AccountMove(models.Model):
    """
    Add uuid to account.move
    """

    _name = "account.move"
    _inherit = ["account.move", "res.uuid"]


class AccountMoveLine(models.Model):
    """
    Add uuid to account.move.line
    """

    _name = "account.move.line"
    _inherit = ["account.move.line", "res.uuid"]
