from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    is_allow_split_mo = fields.Boolean(
        string="Allow Split Mo",
        default=True,
    )
