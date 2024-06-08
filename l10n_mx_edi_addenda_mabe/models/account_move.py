from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # New Fields
    mabe_ref1 = fields.Char(string="Mabe Reference 1", default="NA")
    mabe_ref2 = fields.Char(string="Mabe Reference 2", default="NA")
    mabe_amount_with_letter = fields.Char(string="Amount with letter")
    mabe_flag = fields.Boolean(default=False, compute="_compute_mabe_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda_name")
    def _compute_mabe_flag(self):
        for record in self:
            record.mabe_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Mabe"
            )
