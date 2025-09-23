# Import Odoo libs
from odoo import _, api, fields, models


class MRPProduction(models.Model):
    """
    Inherit the Manufacturing Order (MRP Production) model to add
    credit limit logic and integrate with exception rules.
    """

    _inherit = "mrp.production"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        string="Credit Hold",
        store=True,
        compute="_compute_credit_hold",
        help="Indicates whether this Manufacturing Order is on hold due to "
        "credit issues inherited from the related Sales Order.",
    )

    # END #########
    # METHODS #####

    def update_ignore_exceptions(self):
        """
        Force-set 'ignore_exception' to True on this MO.

        This method bypasses Odoo ORM for performance reasons and
        updates the database directly using SQL. It is used when the
        credit hold is released, so exceptions should no longer block
        processing.
        """
        if not self.ids:
            return False

        query = """
            UPDATE mrp_production 
            SET ignore_exception = TRUE 
            WHERE id IN %s
        """

        # Execute raw SQL update to quickly set ignore_exception flag
        self.env.cr.execute(query, (tuple(self.ids),))
        return True

    @api.depends(
        "sale_order_id",
        "sale_order_id.credit_hold",
        "sale_order_id.override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        """
        Compute method for 'credit_hold'.

        - Pulls credit hold status from the related Sale Order.
        - If the Sale Order is NOT on credit hold, automatically mark
          exceptions on the MO as ignored (so it can proceed).
        """
        for mo in self:
            # Credit hold comes directly from the linked sale order
            mo.credit_hold = bool(mo.sale_order_id.credit_hold)

            # If no credit hold applies, exceptions should be ignored
            if not mo.credit_hold:
                mo.update_ignore_exceptions()

    # END #########
