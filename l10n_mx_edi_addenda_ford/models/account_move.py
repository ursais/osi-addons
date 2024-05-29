from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # New Fields
    ford_ref = fields.Char(string="Reference", default="NA")
    ford_flag = fields.Boolean(default=False, compute="_compute_flag")

    @api.depends("partner_id.l10n_mx_edi_addenda_name")
    def _compute_flag(self):
        for record in self:
            record.ford_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Ford"
            )
