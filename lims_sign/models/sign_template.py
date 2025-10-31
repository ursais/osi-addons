from odoo import fields, models


class SignTemplate(models.Model):
    _inherit = "sign.template"

    is_default_lims_template = fields.Boolean(
        string="Default LIMS Template",
        help="If checked, this template will be used as the default when sending "
        "LIMS documents for signature.",
    )
