# Import Odoo libs
from random import randint

from odoo import fields, models


class RMASupplierTag(models.Model):
    """New supplier RMA tags object."""

    _name = "rma.supplier.tag"
    _description = "RMA Tag"

    def _get_default_color(self):
        return randint(1, 11)

    # FIELD DEFAULT METHOD ######

    name = fields.Char("Tag Name", required=True, translate=True)
    color = fields.Integer("Color", default=_get_default_color)

    # END ##########
    # CONSTRANTS ######

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Tag name already exists!"),
    ]

    # END ##########
