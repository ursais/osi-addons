# Import Odoo Libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit the Object for Field adding."""

    _inherit = "product.template"

    # COLUMNS #####

    is_constrained = fields.Boolean(
        string="Is Constrained?",
        help="Use sale order confirmation date instead of scheduled date for availability forecasting.",
        groups="stock.group_stock_user",
        company_dependent=True,
    )

    # END #########
    # METHODS #####

    def set_is_constrained(self):
        active_ids = self.browse(self._context.get("active_ids"))
        if "is_constrained" in self._context:
            active_ids.write({"is_constrained": self._context.get("is_constrained")})

    def write(self, vals):
        """If the is_constrained is being changed then update all open stock.moves accordingly."""
        res = super().write(vals)

        if "is_constrained" in vals:
            for template in self:
                variant_ids = template.product_variant_ids.ids
                if not variant_ids:
                    continue

                if vals["is_constrained"]:
                    # CASE 1: update from sale_line_id.order_id.date_confirm
                    self.env.cr.execute(
                        """
                        UPDATE stock_move sm
                        SET date = so.date_confirm
                        FROM sale_order_line sol
                        JOIN sale_order so ON sol.order_id = so.id
                        WHERE sm.sale_line_id = sol.id
                        AND sm.product_id = ANY(%s)
                        AND sm.state NOT IN ('done', 'cancel')
                        AND so.date_confirm IS NOT NULL
                    """,
                        [variant_ids],
                    )

                    # CASE 2: update from raw_material_production_id.sale_order_id.date_confirm
                    self.env.cr.execute(
                        """
                        UPDATE stock_move sm
                        SET date = so.date_confirm
                        FROM mrp_production mo
                        JOIN sale_order so ON mo.sale_order_id = so.id
                        WHERE sm.raw_material_production_id = mo.id
                        AND sm.product_id = ANY(%s)
                        AND sm.state NOT IN ('done', 'cancel')
                        AND so.date_confirm IS NOT NULL
                    """,
                        [variant_ids],
                    )

                else:
                    # CASE 3: revert to production.date_start or picking.scheduled_date or now
                    now_str = fields.Datetime.now().isoformat()

                    # 1. Update MO-related moves with mo.date_start
                    self.env.cr.execute(
                        """
                        UPDATE stock_move sm
                        SET date = mo.date_start
                        FROM mrp_production mo
                        WHERE sm.raw_material_production_id = mo.id
                        AND sm.product_id = ANY(%s)
                        AND sm.state NOT IN ('done', 'cancel')
                        AND mo.date_start IS NOT NULL
                    """,
                        [variant_ids],
                    )

                    # 2. Update SO-related moves with picking.scheduled_date
                    self.env.cr.execute(
                        """
                        UPDATE stock_move sm
                        SET date = sp.scheduled_date
                        FROM stock_picking sp
                        WHERE sm.picking_id = sp.id
                        AND sm.product_id = ANY(%s)
                        AND sm.state NOT IN ('done', 'cancel')
                        AND sm.sale_line_id IS NOT NULL
                        AND sp.scheduled_date IS NOT NULL
                    """,
                        [variant_ids],
                    )

                    # 3. Fallback to now() for any remaining
                    self.env.cr.execute(
                        """
                        UPDATE stock_move
                        SET date = %s
                        WHERE product_id = ANY(%s)
                        AND state NOT IN ('done', 'cancel')
                        AND date IS NULL
                    """,
                        [now_str, variant_ids],
                    )

        return res

    # END #########
