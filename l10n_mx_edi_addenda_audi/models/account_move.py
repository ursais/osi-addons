from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    unidad_negocio = fields.Char(string="Unidad de negocio")
    email_solicitante = fields.Char(string="Email del solicitante")

