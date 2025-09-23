# Import Odoo Libs
from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    """
    Update purchase order lines with fields
    """

    _inherit = "purchase.order.line"

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # END #########
    # METHODS ######

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
        res["note"] = self.note
        return res

    @api.depends("product_qty", "product_uom", "company_id")
    def _compute_price_unit_and_date_planned_and_name(self):
        """
        Compute the `price_unit`, `date_planned`, and `name` fields for purchase order lines.

        This override skips computation for lines that are:
        - Already in 'purchase' state (confirmed), **and**
        - Already have a `price_unit` set

        This avoids overwriting confirmed data during recomputation, which can happen
        if dependent fields like `product_qty` or `product_uom` are changed.
        """
        # Exclude lines that are already confirmed and have price_unit set
        self = self - self.filtered(
            lambda l: l.order_id.state == "purchase" and l.price_unit
        )
        # Call the original compute method for the remaining records
        return super(
            PurchaseOrderLine, self
        )._compute_price_unit_and_date_planned_and_name

    def write(self, values):
        """
        Re-implement the important parts of core write but skip the
        move-deadline update when invoked with skip_move_sync in context.

        IMPORTANT: we call models.Model.write(...) (raw ORM write) to avoid
        re-entering the core purchase.order.line.write() which would itself
        call _update_move_date_deadline() before the write and cause recursion.
        """
        # Respect context flag: if skip_move_sync is present we must NOT call
        # the core behavior that updates moves before the write.
        if values.get("date_planned") and not self.env.context.get("skip_move_sync"):
            new_date = fields.Datetime.to_datetime(values["date_planned"])
            self.filtered(lambda l: not l.display_type)._update_move_date_deadline(
                new_date
            )

        # lines that are in 'purchase' state (same as core logic)
        lines = self.filtered(
            lambda l: l.order_id.state == "purchase" and not l.display_type
        )

        # product_packaging_id update matches core: assign on draft moves
        if "product_packaging_id" in values:
            self.move_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            ).product_packaging_id = values["product_packaging_id"]

        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        previous_product_qty = {line.id: line.product_qty for line in lines}

        # do the raw ORM write to avoid invoking parent's purchase.order.line.write() (which
        # contains its own move-update logic that would re-trigger stock.move.write())
        result = models.Model.write(self, values)

        # follow-up logic copied from core
        if "price_unit" in values:
            for line in lines:
                # Avoid updating kit components' stock.move
                moves = line.move_ids.filtered(
                    lambda s: s.state not in ("cancel", "done")
                    and s.product_id == line.product_id
                )
                moves.write({"price_unit": line._get_stock_move_price_unit()})

        if "product_qty" in values:
            changed = lines.filtered(
                lambda l: float_compare(
                    previous_product_qty[l.id],
                    l.product_qty,
                    precision_rounding=l.product_uom.rounding,
                )
                != 0
            )
            changed.with_context(
                previous_product_qty=previous_product_uom_qty
            )._create_or_update_picking()

        return result

    # END ##########
