# Copyright (C) 2019, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import date, timedelta
from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    def _prepare_subscription_data(self, template):
        """
        Fix possible Odoo bug:
        the initial next invoice date should be now,
        not next month
        """
        res = super()._prepare_subscription_data(template)
        res['recurring_next_date'] = res['date_start']
        return res
