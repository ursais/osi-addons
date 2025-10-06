# Import Odoo libs
from odoo import _, api, fields, models


class StockPicking(models.Model):
    """
    Inherit Stock Picking to integrate Credit Limit checks.

    Adds:
      - `credit_hold`: Boolean flag inherited from the related Sale Order.
      - Automatic update of ignore_exception when no credit hold exists.
    """

    _inherit = "stock.picking"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold",
        store=True,
        compute="_compute_credit_hold",
        help="Indicates whether this picking is blocked due to credit hold "
        "on the related Sale Order.",
    )

    # END #########
    # METHODS #####
    def update_ignore_exceptions(self):
        """
        Force-enable `ignore_exception` on this picking.
        """
        self.ensure_one()
        if not self.ids:
            return 

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
        """
        Compute credit hold for Stock Pickings.

        Rules:
          - Inherit credit hold status from the linked Sale Order.
          - If the picking is NOT on credit hold, automatically
            mark `ignore_exception` so that exception rules won’t
            block the picking unnecessarily.
        """
        for pick in self:
            pick.credit_hold = bool(pick.sale_id.credit_hold)
            if not pick.credit_hold:
                pick.update_ignore_exceptions()

    # # END #########
