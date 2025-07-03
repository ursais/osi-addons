# Import Odoo Libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Add related hot_ar field to trigger exception checks."""

    _inherit = "sale.order"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        related="partner_invoice_id.commercial_partner_id.hot_ar",
        store=True,
        help="""Customer hot AR status""",
    )

    # END #########
    # METHODS #####

    def trigger_all_exception_checks(self):
        """Triggers exception checks on sale order, related stock pickings, and related MOs."""
        self.detect_exceptions()

        # Stock Transfers
        transfers = self.mapped("picking_ids").filtered_domain(
            [("state", "not in", ("done", "cancel"))]
        )
        if transfers:
            transfers.detect_exceptions()

        # Manufacturing Orders via procurement chain
        MrpProduction = self.env["mrp.production"]
        related_mos = MrpProduction

        for sale in self:
            pg = sale.procurement_group_id
            if pg:
                related_mos |= (
                    pg.stock_move_ids.created_production_id | pg.mrp_production_ids
                )

        related_mos = MrpProduction.browse(related_mos.ids).filtered_domain(
            [("state", "not in", ("done", "progress", "to_close", "cancel"))]
        )
        if related_mos:
            related_mos.detect_exceptions()

    # END #########
