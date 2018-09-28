# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_extra_move_vals(self, qty):
        raise ValidationError(
            _("The quantity done cannot be greater than the quantity "
              "reserved."))
