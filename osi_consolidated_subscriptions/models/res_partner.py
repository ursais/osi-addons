# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, models, fields, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_invoice_date = fields.Date('Last Invoiced On')
    # Duration of overdue limit
    authoritative_bill_date = fields.\
        Selection([
                   ('1', '1st of the Month'),
                   ('2', '2nd of the Month'),
                   ('3', '3rd of the Month'),
                   ('4', '4th of the Month'),
                   ('5', '5th of the Month'),
                   ('6', '6th of the Month'),
                   ('7', '7th of the Month'),
                   ('8', '8th of the Month'),
                   ('9', '9th of the Month'),
                   ('10', '10th of the Month'),
                   ('11', '11th of the Month'),
                   ('12', '12th of the Month'),
                   ('13', '13th of the Month'),
                   ('14', '14th of the Month'),
                   ('15', '15th of the Month'),
                   ('16', '16th of the Month'),
                   ('17', '17th of the Month'),
                   ('18', '18th of the Month'),
                   ('19', '19th of the Month'),
                   ('20', '20th of the Month'),
                   ('21', '21st of the Month'),
                   ('22', '22nd of the Month'),
                   ('23', '23rd of the Month'),
                   ('24', '24th of the Month'),
                   ('25', '25th of the Month'),
                   ('26', '26th of the Month'),
                   ('27', '27th of the Month'),
                   ('28', '28th of the Month'),
                   ('29', '29th of the Month'),
                   ('30', '30th of the Month'),
                   ('eom', 'End of the Month')],
        string='Authoritative Bill Date',
        required=True,
        readonly=True,
        default='1',
        help='Specify the date this partner record will have \
        all of his/her subscriptions billed on')

    def action_open_change_date_wizard(self):
        view = self.env.ref('osi_consolidated_subscriptions.res_partner_change_bill_date_form')
        wiz = self.env['res.partner.change.bill.date'].create([])
        return {
            'name': _('Change Bill Date'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner.change.bill.date',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

    def cron_consolidate_invoices(self):
        contact_ids = self.search([('customer', '=', True)])
        # Loop through Contacts
        for contact_id in contact_ids:
            # If today is this partner's ABD and they have at least 1 open invoice
            if (contact_id.authoritative_bill_date == date.today().day) and \
                    (self.env['account.invoice'].search_count([('partner_id', '=', contact_id.id),('state_id')]) > 0):
                contact_id.last_invoice_date = date.today()
                inv = self.env['account.invoice.consolidated'].\
                    create(contact_id.cron_prepare_consolidated_invoice_values())
                inv.get_invoices()
                inv.get_invoice_price()
                inv.action_confirm_invoice()

    def cron_prepare_consolidated_invoice_values(self):
        return {
                'partner_id': self.id,
                'date_from': datetime.today() - relativedelta(months=3),
                'date_to': datetime.today(),
                'company_id': self.env.user.company_id.id}
