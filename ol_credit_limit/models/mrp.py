# Import Odoo libs
from odoo import _, api, fields, models


class MRPProduction(models.Model):
    """
    Inherit MRP Prodduction Object to add Credit Limit.
    """

    _inherit = "mrp.production"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold", store=True, compute="_compute_credit_hold"
    )

    # END #########
    # METHODS #####

    def update_ignore_exceptions(self):
        self.ensure_one()
        query = """
            UPDATE mrp_production 
            SET ignore_exception = TRUE 
            WHERE id IN %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

    @api.depends(
        "sale_order_id",
        "sale_order_id.credit_hold",
        "sale_order_id.override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        for mo in self:
            credit_hold = False
            if mo.sale_order_id:
                credit_hold = bool(mo.sale_order_id.credit_hold)
            mo.credit_hold = credit_hold
            if not mo.credit_hold:
                mo.update_ignore_exceptions()

    # END #########
