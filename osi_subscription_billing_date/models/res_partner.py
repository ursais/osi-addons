# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # last_invoice_date = fields.Date('Last Invoiced On')
    # Duration of overdue limit
    authoritative_bill_date = fields.Selection(
        [('1', '1st of the Month'),
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
        help='Specify the date this partner record will have \
        all of his/her subscriptions billed on')
