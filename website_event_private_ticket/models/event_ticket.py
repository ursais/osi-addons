from odoo import api, fields, models

class EventTicket(models.Model):
    _inherit = 'event.event.ticket'

    published = fields.Boolean(string='Published', default=True)
