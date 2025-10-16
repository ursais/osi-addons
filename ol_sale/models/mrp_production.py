# Import Odoo libs
from odoo import fields, models


class MrpProduction(models.Model):
    """Add new field to Manufacturing Orders."""

    _inherit = "mrp.production"

    # COLUMNS #####

    mrp_note = fields.Text(
        string="Manufacturing Note",
        related="sale_order_id.mrp_note",
        store=True,
    )
    date_change_exception = fields.Boolean(
        string="Customer Request Date Change Proposed", default=False
    )

    def write(self, vals):
        res = super().write(vals)
        for mo in self:
            if ("mrp_batch_id" in vals or "state" in vals) and mo.sale_order_id:
                mo.sale_order_id._compute_current_estimate_ship_date()
        return res

    # END #########
