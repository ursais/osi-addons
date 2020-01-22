# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models, fields
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_invoice_date = fields.Date('Last Invoiced On')

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
                # TODO: where are the below methods implemented?
                inv.get_invoices()
                inv.get_invoice_price()
                inv.action_confirm_invoice()

    def cron_prepare_consolidated_invoice_values(self):
        return {
                'partner_id': self.id,
                # Why the arbitrary 3 months? Should it be the lats invoice date instead?
                'date_from': datetime.today() - relativedelta(months=3),
                'date_to': datetime.today(),
                # Why use User's company? The invoices migh belong to a different company.
                'company_id': self.env.user.company_id.id}
