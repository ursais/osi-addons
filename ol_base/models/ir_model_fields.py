# Copyright 2020 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    ttype = fields.Selection(
        selection_add=[
            ("nullable_integer", "Nullable Integer"),
            ("nullable_float", "Nullable Float"),
        ],
        ondelete={"nullable_integer": "cascade", "nullable_float": "cascade"},
    )
