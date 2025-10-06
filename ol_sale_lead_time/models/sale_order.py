# Import Odoo libs
from datetime import timedelta
from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    first_estimated_ship_date = fields.Date(
        string="First Estimated Ship Date",
        readonly=True,
        copy=False,
    )

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order.action_compute_esd()
            if not order.first_estimated_ship_date and order.expected_date:
                order.first_estimated_ship_date = order.expected_date.date()
        return res

    @api.depends("order_line.customer_lead", "date_order", "state")
    def _compute_expected_date(self):
        super()._compute_expected_date()
        for order in self:
            if order.expected_date:
                weekday = order.expected_date.weekday()
                if weekday == 5:
                    order.expected_date += timedelta(days=2)
                elif weekday == 6:
                    order.expected_date += timedelta(days=1)

    def _get_virtual_avail_date(self, product, qty):
        today = fields.Date.today()
        qty_available = product.with_context(to_date=today).qty_available
        if qty_available >= qty:
            return today

        incoming_moves = self.env["stock.move"].search(
            [
                ("product_id", "=", product.id),
                ("state", "in", ("confirmed", "assigned", "waiting")),
                ("location_dest_id.usage", "=", "internal"),
                ("picking_type_id.code", "=", "incoming"),
            ],
            order="date_deadline asc",
        )

        running_total = qty_available
        for move in incoming_moves:
            running_total += move.product_uom_qty
            if running_total >= qty:
                return fields.Date.to_date(move.date_deadline)

        return today

    def action_compute_esd(self):
        for order in self:
            order.order_line._compute_customer_lead()

    def _set_dynamic_lead_times(self):
        """Compute customer_lead for all lines in this order,
        considering shared BOM components and availability."""
        today = fields.Date.today()

        for order in self:
            # --- Step 1: Build component requirements map ---
            component_demand = {}  # {product_id: total_qty}
            line_components = {}  # {line_id: [product_id, ...]}

            for line in order.order_line:
                required_qty = line.product_uom_qty
                comps = []

                if line.bom_id:
                    for comp in line.bom_id.bom_line_ids:
                        comp_qty = required_qty * comp.product_qty
                        component_demand[comp.product_id.id] = (
                            component_demand.get(comp.product_id.id, 0) + comp_qty
                        )
                        comps.append(comp.product_id.id)
                    line_components[line.id] = comps

                elif line.product_id.type == "product":
                    # stockable product without BOM
                    component_demand[line.product_id.id] = (
                        component_demand.get(line.product_id.id, 0) + required_qty
                    )
                    line_components[line.id] = [line.product_id.id]

                else:
                    line_components[line.id] = []

            # --- Step 2: Compute availability dates for all components ---
            product_avail = {}
            for product_id, qty in component_demand.items():
                product = self.env["product.product"].browse(product_id)
                avail_date = order._get_virtual_avail_date(product, qty)
                product_avail[product_id] = avail_date and avail_date or today

            # --- Step 3: Assign line-level customer_lead ---
            for line in order.order_line:
                if not line_components[line.id]:
                    line.customer_lead = 0
                    continue
                comp_dates = [product_avail[pid] for pid in line_components[line.id]]
                base_date = comp_dates and max(comp_dates) or today
                lead_days = (base_date - today).days

                # Add rush/manufacturing delays
                if order.rush_order:
                    rush_days = order.company_id.rush_lead_time
                    lead_days += rush_days
                    mfg_sec = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .get_param("mrp.use_manufacturing_lead", 0)
                    )
                    if mfg_sec:
                        lead_days += order.company_id.manufacturing_lead
                else:
                    lead_days += line.bom_id.produce_delay
                    mfg_sec = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .get_param("mrp.use_manufacturing_lead", 0)
                    )
                    if mfg_sec:
                        lead_days += order.company_id.manufacturing_lead

                line.customer_lead = max(0, lead_days)
