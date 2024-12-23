# Import Odoo libs
from odoo import _, api, fields, models


class MRPProduction(models.Model):
    """
    Inherit MRP Prodduction Object to add Credit Limit.
    """

    _inherit = "mrp.production"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold", store=True,compute="_compute_credit_hold" 
    )

    # END #########
    # METHODS #####

    def update_ignore_exceptions(self):
        self.write({"ignore_exception": True})

    @api.depends("sale_order_id","sale_order_id.credit_hold" ,"sale_order_id.override_credit_limit_hold")
    def _compute_credit_hold(self):
        for mo in self:
            credit_hold = False
            if mo.sale_order_id.credit_hold:
                credit_hold = True
            mo.credit_hold = credit_hold
            if not credit_hold:
                mo.update_ignore_exceptions()
            

    # END #########
