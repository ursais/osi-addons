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
        if not self.ids:
            return False

        query = """
            UPDATE mrp_production 
            SET ignore_exception = TRUE 
            WHERE id IN %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))
        return True

    @api.depends(
        "sale_order_id",
        "sale_order_id.credit_hold",
        "sale_order_id.override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        for mo in self:
            mo.credit_hold = bool(mo.sale_order_id.credit_hold)
            if not mo.credit_hold:
                mo.update_ignore_exceptions()

    # END #########
