# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class SignSendRequest(models.TransientModel):
    _inherit = "sign.send.request"

    fsm_order_id = fields.Many2one("fsm.order", "FSM Order")

    def send_request(self):
        res = super(SignSendRequest, self).send_request()
        if res.get("context") and self.fsm_order_id:
            request = self.env["sign.request"].browse(res.get("context").get("id"))
            request.fsm_order_id = self.fsm_order_id.id
        return res
