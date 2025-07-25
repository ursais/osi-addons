# Import Odoo libs
from odoo import _, models


class StockScrap(models.Model):
    """Inherit scrap to add confirm wizard if scrapping reserved material."""

    _inherit = "stock.scrap"

    # METHODS #####

    def action_validate(self):
        """Add confirmation wizard if scrapping is going to affect allocations."""
        self.ensure_one()

        qty = self.scrap_qty
        available_qty = self.with_context(
            location=self.location_id.id,
            lot_id=self.lot_id.id,
            package_id=self.package_id.id,
            owner_id=self.owner_id.id,
            strict=True,
        ).product_id.qty_available
        if available_qty and self.product_id.virtual_available < qty:
            ctx = dict(self.env.context)
            ctx.update(
                {
                    "active_id": self.id,
                    "scrap_qty": qty,
                    "product_id": self.product_id.id,
                }
            )
            return {
                "name": _("Confirm Scrap"),
                "type": "ir.actions.act_window",
                "res_model": "stock.scrap.confirm.wizard",
                "view_id": self.env.ref("ol_stock.view_scrap_confirm_wizard").id,
                "view_mode": "form",
                "target": "new",
                "context": ctx,
            }

        return super().action_validate()

    # END #########
