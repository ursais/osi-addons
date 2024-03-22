from odoo import api, fields, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    ap_partner_id = fields.Many2one('res.partner', compute='_compute_ap_partner_id')

    @api.depends('partner_id')
    def _compute_ap_partner_id(self):
        for rec in self:
            if rec.partner_id.type == 'ap_address':
                rec.ap_partner_id = rec.partner_id
            elif rec.partner_id.child_ids.filtered(lambda p: p.type=='ap_address'):
                rec.ap_partner_id = rec.partner_id.child_ids.filtered(lambda p: p.type=='ap_address')[0]
            elif rec.partner_id.parent_id.child_ids.filtered(lambda p: p.type=='ap_address'):
                rec.ap_partner_id = rec.partner_id.parent_id.child_ids.filtered(lambda p: p.type=='ap_address')[0]
            else:
                rec.ap_partner_id = rec.partner_id


    def _check_build_page_info(self, i, p):
        """
        Inheriting to change the partne ron Checks to AP vendor type contact
        """

        res = super()._check_build_page_info(i, p)
        res['partner_id'] = self.ap_partner_id
        res['partner_name'] = self.ap_partner_id.name
        return res
