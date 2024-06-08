from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # New Fields
    ford_ref = fields.Char(string="Ford Reference", default="NA")
    ford_flag = fields.Boolean(compute="_compute_ford_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda")
    def _compute_ford_flag(self):
        for record in self:
            record.ford_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Ford"
            )
