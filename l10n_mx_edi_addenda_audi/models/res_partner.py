from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    audi_supplier_email = fields.Char(string="Supplier Email")
    audi_supplier_number = fields.Char(string="Supplier Number")
