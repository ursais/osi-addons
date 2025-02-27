# Import Odoo libs
from odoo import _, api, fields, models


class StockPicking(models.Model):
    """
    Inherit Stock Picking Object to add Credit Limit.
    """

    _inherit = "stock.picking"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold",
        store=True,
        compute="_compute_credit_hold",
    )

    # END #########
    # METHODS #####
    def update_ignore_exceptions(self):
        self.ensure_one()
        query = """
            UPDATE stock_picking 
            SET ignore_exception = TRUE 
            WHERE id IN %s
        """
        self.env.cr.execute(query, (tuple(self.ids),))

    @api.depends(
        "sale_id.credit_hold",
        "sale_id.override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        for pick in self:
            pick.credit_hold = bool(pick.sale_id.credit_hold)
            if not pick.credit_hold:
                pick.update_ignore_exceptions()

    # # END #########
