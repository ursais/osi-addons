# Import Odoo libs
from odoo import _, api, fields, models


class StockPicking(models.Model):
    """
    Inherit Stock Picking Object to add Credit Limit.
    """

    _inherit = "stock.picking"

    # COLUMNS #####

    credit_hold = fields.Boolean("Credit Hold",store=True,compute="_compute_credit_hold" )

    # END #########
    # METHODS #####

    def update_ignore_exceptions(self):
        self.write({"ignore_exception": True})

    @api.depends("sale_id","sale_id.credit_hold", "sale_id.override_credit_limit_hold")
    def _compute_credit_hold(self):
        for pick in self:
            credit_hold = False
            if pick.sale_id.credit_hold:
                credit_hold = True
            pick.credit_hold = credit_hold
            if not credit_hold:
                pick.update_ignore_exceptions()

    # # END #########
