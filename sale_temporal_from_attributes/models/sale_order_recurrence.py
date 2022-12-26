# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class SaleOrderRecurrence(models.Model):
    _inherit = "sale.temporal.recurrence"

    factor = fields.Float(default=1.0)
