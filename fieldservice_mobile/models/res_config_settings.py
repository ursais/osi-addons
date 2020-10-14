# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fsm_allow_portal_view_move_qty = fields.Boolean(
        string='Allow portal user to view stock move quantities')
    fsm_allow_portal_update_move_qty = fields.Boolean(
        string='Allow portal user update of stock move quantities')
    fsm_allow_portal_validate_move_qty = fields.Boolean(
        string='Allow portal user validation of stock move quantities')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            fsm_allow_portal_view_move_qty=bool(params.get_param(
                'fieldservice_mobile.fsm_allow_portal_view_move_qty')
            ) or False,
            fsm_allow_portal_update_move_qty=bool(params.get_param(
                'fieldservice_mobile.fsm_allow_portal_update_move_qty')
            ) or False,
            fsm_allow_portal_validate_move_qty=bool(params.get_param(
                'fieldservice_mobile.fsm_allow_portal_validate_move_qty')
            ) or False,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'fieldservice_mobile.fsm_allow_portal_view_move_qty',
            self.fsm_allow_portal_view_move_qty)
        self.env['ir.config_parameter'].sudo().set_param(
            'fieldservice_mobile.fsm_allow_portal_update_move_qty',
            self.fsm_allow_portal_update_move_qty)
        self.env['ir.config_parameter'].sudo().set_param(
            'fieldservice_mobile.fsm_allow_portal_validate_move_qty',
            self.fsm_allow_portal_validate_move_qty)
