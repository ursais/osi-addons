# Import Odoo libs
from odoo import api, models


class DeliveryCarrierMultiplier(models.Model):
    """
    Adding functionality to compute Last PO Margin
    on products when multiplier changes.
    """

    _inherit = "delivery.carrier.multiplier"

    # METHODS ##########

    def write(self, vals):
        """When the multiplier value changes, the last purchase margin on all
        products that have this multiplier needs to be computed."""
        res = super().write(vals)
        for rec in self:
            if "multiplier" in vals:
                products = self.env["product.template"].search(
                    [("carrier_multiplier_id", "=", rec.id)]
                )
                products._compute_last_purchase_margin()
        return res

    # END ##########
