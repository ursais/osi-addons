from odoo import _, api, fields, models
from odoo.exceptions import UserError

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.depends('composition_mode', 'model', 'parent_id', 'res_domain',
                 'res_ids', 'template_id')
    def _compute_partner_ids(self):
        super()._compute_partner_ids()
        for composer in self:
            account_payment = self.env["account.payment"].browse(self._context.get("active_id"))
            if account_payment.payment_type == "outbound":
                ar_contacts  = self.env["res.partner"].search([("ar","=",True),("id","child_of",composer.partner_ids.ids)])
                if not ar_contacts:
                    raise UserError(_(
                        """No ‘AR’ contacts are found,
                        please add or set the ‘AR’ setting on a contact and try again."""
                    ))
                composer.partner_ids = composer.partner_ids.ids + ar_contacts.ids
