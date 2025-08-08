# Import Odoo libs
from math import floor, inf
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    """Inherit SO Line to add backorder qty functionality."""

    _inherit = "sale.order.line"

    # METHODS #####

    # ------------------------------
    # HELPER METHODS
    # ------------------------------

    def _get_free_available_in_uom(self, product, location, uom):
        """
        Get the quantity of a product available at a given location,
        excluding reserved quantities, converted into the target UoM.

        Args:
            product (product.product): Product to check.
            location (stock.location): Location to check.
            uom (uom.uom): Unit of measure to convert to.

        Returns:
            float: Available quantity in the requested UoM.
        """
        Quant = self.env["stock.quant"].sudo()
        free = Quant._get_available_quantity(
            product,
            location,
            lot_id=False,
            package_id=False,
            owner_id=False,
            strict=True,  # Strict means only exact location, no hierarchy search.
        )
        return product.uom_id._compute_quantity(free, uom, rounding_method="DOWN")

    def _is_stockable(self, product):
        """
        Check if a product is stockable (type 'product').

        Args:
            product (product.product): Product to check.

        Returns:
            bool: True if stockable, False otherwise.
        """
        return product.detailed_type == "product"

    def _get_peer_committed_qty(self):
        """
        Get the total quantity of the same product from other lines
        in the same sale order, expressed in the current line's UoM.

        Returns:
            float: Quantity committed by peers.
        """
        self.ensure_one()
        if not self.product_id or not self.order_id:
            return 0.0
        total = 0.0
        for peer in self.order_id.order_line:
            if peer == self or peer.display_type:
                continue
            if peer.product_id == self.product_id:
                total += peer.product_uom._compute_quantity(
                    peer.product_uom_qty, self.product_uom, rounding_method="UP"
                )
        return total

    def _get_incoming_qty(self, product, location, before_date):
        """
        Get total incoming quantity for a product to a given location,
        with moves scheduled before or on a given date.

        Args:
            product (product.product): Product to check.
            location (stock.location): Destination location.
            before_date (date): Cutoff date for moves.

        Returns:
            float: Incoming quantity in the product's default UoM.
        """
        Move = self.env["stock.move"].sudo()
        incoming_moves = Move.search(
            [
                ("product_id", "=", product.id),
                ("state", "in", ("confirmed", "assigned", "partially_available")),
                ("location_dest_id", "child_of", location.id),
                ("date", "<=", before_date),
            ]
        )
        qty = sum(
            move.product_uom._compute_quantity(
                move.product_uom_qty, product.uom_id, rounding_method="UP"
            )
            for move in incoming_moves
        )
        return qty

    def _get_incoming_summary(self, product_entries, cutoff_date):
        """
        Build a human-readable summary of incoming stock for given products.

        Args:
            product_entries (list): Tuples of (product, location, label).
            cutoff_date (date): Date to separate 'before' and 'after' incoming stock.

        Returns:
            str: Summary text for user-facing messages.
        """
        Move = self.env["stock.move"].sudo()
        incoming_by_key = defaultdict(list)

        # Fetch and group incoming moves
        for product, location, label in product_entries:
            moves = Move.search(
                [
                    ("product_id", "=", product.id),
                    ("state", "in", ("confirmed", "assigned", "partially_available")),
                    ("location_dest_id", "child_of", location.id),
                ],
                order="date asc",
            )
            for m in moves:
                qty = m.product_uom._compute_quantity(
                    m.product_uom_qty, product.uom_id, rounding_method="UP"
                )
                incoming_by_key[(product, label)].append((qty, m.date))

        lines = []
        for product, location, label in product_entries:
            move_data = incoming_by_key.get((product, label), [])
            sku = product.default_code or product.display_name

            if not move_data:
                # No incoming stock at all
                lines.append(
                    _("%s %s has no available stock and no incoming purchase orders.")
                    % (label, sku)
                )
                continue

            # Split incoming moves into before and after commitment date
            before = [(q, d) for q, d in move_data if d <= cutoff_date]
            after = [(q, d) for q, d in move_data if d > cutoff_date]

            if before:
                total = sum(q for q, _ in before)
                earliest = min(d for _, d in before)
                lines.append(
                    _("%s %s has %s units incoming on %s.")
                    % (label, sku, int(total), earliest.strftime("%Y-%m-%d"))
                )

            if after:
                total = sum(q for q, _ in after)
                earliest = min(d for _, d in after)
                lines.append(
                    _(
                        "%s %s has %s additional units expected after the commitment date, earliest on %s."
                    )
                    % (label, sku, int(total), earliest.strftime("%Y-%m-%d"))
                )

        return "\n".join(lines)

    def _compute_bom_limited_qty(self, product, bom, location, line_uom):
        """
        Compute the maximum sellable quantity for a BOM-based product,
        considering available stock + incoming for each component.

        Args:
            product (product.product): Finished product.
            bom (mrp.bom): Bill of Materials record.
            location (stock.location): Stock location.
            line_uom (uom.uom): UoM of the sale order line.

        Returns:
            tuple: (max_qty, limiting_components)
        """
        if not bom:
            return inf, []

        components = bom.bom_line_ids
        qty_base = product.uom_id._compute_quantity(1.0, bom.product_uom_id)
        max_units = inf
        limiting_components = []

        commitment_date = self.order_id.commitment_date or fields.Date.today()

        for bom_line in components:
            comp = bom_line.product_id
            if not comp or not self._is_stockable(comp):
                continue
            if getattr(comp, "allow_backorder", True):
                continue

            comp_uom = bom_line.product_uom_id
            qty_per_unit = comp_uom._compute_quantity(
                bom_line.product_qty * qty_base, comp.uom_id, rounding_method="UP"
            )
            if qty_per_unit <= 0:
                continue

            # Available now + incoming before commitment date
            comp_free = self._get_free_available_in_uom(comp, location, comp.uom_id)
            incoming = self._get_incoming_qty(comp, location, commitment_date)
            total_available = comp_free + incoming

            units_by_comp = floor(total_available / qty_per_unit)

            if units_by_comp < max_units:
                max_units = units_by_comp
                limiting_components = [(comp, location, "Component")]
            elif units_by_comp == max_units:
                limiting_components.append((comp, location, "Component"))

        if max_units in (inf, None):
            return inf, []
        return (
            product.uom_id._compute_quantity(
                max_units, line_uom, rounding_method="DOWN"
            ),
            limiting_components,
        )

    def _compute_product_self_limited_qty(self, product, location, line_uom):
        """
        Compute max sellable qty for a single product (non-BOM),
        considering stock + incoming before commitment date.

        Returns:
            tuple: (max_qty, [(product, location, label)])
        """
        if not self._is_stockable(product):
            return inf, []
        if getattr(product, "allow_backorder", True):
            return inf, []

        commitment_date = self.order_id.commitment_date or fields.Date.today()

        current_free = self._get_free_available_in_uom(
            product, location, product.uom_id
        )
        incoming = self._get_incoming_qty(product, location, commitment_date)
        total = current_free + incoming

        qty = product.uom_id._compute_quantity(total, line_uom, rounding_method="DOWN")
        return qty, [(product, location, "Product")]

    def _max_sellable_qty_now(self):
        """
        Calculate the effective sellable quantity for this order line,
        combining:
          - product-level restriction
          - BOM component restriction
          - already committed quantities in other lines

        Returns:
            tuple: (remaining_qty, sources)
        """
        self.ensure_one()

        if not self.product_id or not self.order_id or self.display_type:
            return inf, []

        loc = self.order_id.warehouse_id.lot_stock_id
        line_uom = self.product_uom or self.product_id.uom_id

        cap_self, src_self = self._compute_product_self_limited_qty(
            self.product_id, loc, line_uom
        )
        cap_bom, src_bom = self._compute_bom_limited_qty(
            self.product_id, self.bom_id, loc, line_uom
        )

        if cap_self == inf and cap_bom == inf:
            return inf, []

        cap_total = (
            min(cap_self, cap_bom)
            if cap_self != inf and cap_bom != inf
            else (cap_self if cap_bom == inf else cap_bom)
        )

        peer = self._get_peer_committed_qty()
        remaining = max(cap_total - peer, 0.0)

        sources = []
        if cap_self != inf:
            sources += src_self
        if cap_bom != inf:
            sources += src_bom
        return remaining, sources

    # ------------------------------
    # ONCHANGE & CONSTRAINTS
    # ------------------------------

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "bom_id",
        "order_id.commitment_date",
    )
    def _onchange_cap_qty_no_backorders(self):
        """
        Prevent user from setting a quantity higher than max sellable
        at order line creation/edit time (UI onchange check).
        """
        for line in self:
            if line.product_id and not line.product_id.allow_backorder:
                max_qty, _ = line._max_sellable_qty_now()
                if line.product_uom_qty > max_qty:
                    raise ValidationError(
                        _(
                            "Product %s is not available to be sold past available quantity of %.2f."
                        )
                        % (line.product_id.display_name, max_qty)
                    )

    @api.constrains(
        "product_id",
        "product_uom_qty",
        "bom_id",
    )
    def _check_no_backorders_caps(self):
        """
        Final validation at record save.
        Raises an error if ordered qty exceeds max sellable qty.
        Also appends incoming stock info to help the user understand availability.
        """
        for line in self:
            if not line.product_id or not line.order_id or line.display_type:
                continue
            cap, sources = line._max_sellable_qty_now()
            if cap is inf:
                continue
            cap = max(cap, 0.0)
            if line.product_uom_qty > cap:
                sku = line.product_id.default_code or line.product_id.display_name
                cutoff = (
                    line.order_id.commitment_date
                    or line.order_id.expected_date
                    or line.order_id.date_order
                )
                incoming_note = line._get_incoming_summary(sources, cutoff)

                msg = _(
                    "Product %(sku)s is not available to be sold past available quantity of %(qty)s.",
                    sku=sku,
                    qty=cap,
                )
                if incoming_note:
                    msg += "\n\n" + incoming_note
                raise ValidationError(msg)

    # END #####
