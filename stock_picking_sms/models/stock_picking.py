# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        pickings = super(StockPicking, self).action_done()
        for picking in self:
            note_msg = _('SMS text message reminder sent !')
            msg = False
            if picking.picking_type_id.code == 'internal':
                msg = "We are glad to inform you that your order " \
                      "n° %s has been shipped." % (picking.origin)
            elif picking.picking_type_id.code == 'outgoing':
                msg = "We are glad to inform you that your order " \
                      "n° %s has been delivered." % (picking.origin)
            if msg:
                picking.message_post_send_sms(msg, note_msg=note_msg)
        return pickings
