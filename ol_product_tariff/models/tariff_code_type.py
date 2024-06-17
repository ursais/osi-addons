# Import Python Libs

# Import Odoo Libs
from odoo import models, fields


class TariffCodeType(models.Model):
    _name = "tariff.code.type"
    _description = "Tariff Code Type"

    # COLUMNS ###
    name = fields.Char(string="Name", required=True)
    label = fields.Char(string="Label", required=True)
    description = fields.Text(string="Description")
    # END #######
