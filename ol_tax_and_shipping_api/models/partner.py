import time
from random import random

from odoo import models


class ResPartner(models.Model):

    _inherit = "res.partner"

    def _get_avatax_customer_code(self):
        """
        Make sure we can handle pseudo records coming from tax & Shipping interfaces
        """
        self.ensure_one()
        if isinstance(self.id, models.NewId):
            record_id = self._origin.id if self._origin else self.id.ref or ""
            return f"{int(time.time())}-{int(random() * 10)}-Cust-{record_id}"

        return super()._get_avatax_customer_code()
