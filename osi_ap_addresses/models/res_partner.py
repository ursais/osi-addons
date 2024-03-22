from odoo import api, fields, models, _
from odoo.exceptions import UserError
class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=[('ap_address', 'AP Address')])



    def write(self, vals):
        res = super().write(vals)
        if self.type == 'ap_address':
            child_ap_contacts = self.parent_id.child_ids.filtered(lambda x: x.type=='ap_address')
            if len(child_ap_contacts) >= 2:
                raise UserError(_("You cannot have more than 1 AP contact as Child record on Main Contact {}.".format(self.parent_id.name)))
        return res


    @api.model_create_multi
    def create(self, val_list):
        records = super().create(val_list)
        for rec in records:
            child_ap_contacts = rec.parent_id.child_ids.filtered(lambda x: x.type=='ap_address')
            if len(child_ap_contacts) >= 2:
                raise UserError(_("You cannot have more than 1 AP contact as Child record on Main Contact {}.".format(rec.parent_id.name)))
        return records
