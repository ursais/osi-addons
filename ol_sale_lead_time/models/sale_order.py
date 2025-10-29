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
    last_esd_date = fields.Date("Last ESD Date")
    esd_warning_message = fields.Html(compute="_compute_esd_warning_message")

    @api.depends("last_esd_date")
    def _compute_esd_warning_message(self):
        for order in self:
            if not order.last_esd_date:
                order.esd_warning_message = False
                continue

            delta_days = (fields.Date.today() - order.last_esd_date).days
            if delta_days > 1:
                order.esd_warning_message = (
                    f"Estimated Ship Date calculated {delta_days} day{'s' if delta_days > 1 else ''} ago. "
                    "The Estimated Ship Date is an estimate at time of calculation and may be outdated."
                )
            else:
                order.esd_warning_message = False

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

        self.env.cr.execute(
            """
                SELECT
                    sm.date_deadline, sm.product_uom_qty
                FROM
                    stock_move sm
                JOIN
                    stock_location sl ON sm.location_dest_id = sl.id
                JOIN
                    stock_picking_type spt ON sm.picking_type_id = spt.id
                WHERE sm.product_id = %s
                AND sm.state IN ('confirmed', 'assigned', 'waiting')
                AND sl.usage = 'internal'
                AND spt.code = 'incoming'
                ORDER BY sm.date_deadline ASC
            """,
            [product.id],
        )

        incoming_moves = self.env.cr.fetchall()

        running_total = qty_available
        for date_deadline, product_uom_qty in incoming_moves:
            running_total += product_uom_qty
            if running_total >= qty:
                return fields.Date.to_date(date_deadline)

        return today

    def action_compute_esd(self):
        for order in self:
            order.last_esd_date = fields.Date.today()
            order.order_line._compute_customer_lead()

    def _set_dynamic_lead_times(self):
        """Compute customer_lead for all lines in this order,
        considering shared BOM components and availability."""
        today = fields.Date.today()
        max_component_delay = False

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
                if not lead_days:
                    bom_data = self.env["report.mrp.report_bom_structure"]._get_report_data(
                        line.bom_id.id
                    )

                    # Get components list from the BOM data
                    components = bom_data.get("lines", {}).get("components", [])

                    max_component_delay = self.env[
                        "report.mrp.report_bom_structure"
                    ]._get_max_component_delay(components)
                    if max_component_delay:
                        lead_days += max_component_delay
                if not lead_days and not max_component_delay:
                    no_po_lead_time = (
                        self.env["ir.config_parameter"]
                        .sudo()
                        .get_param("ol_sale.no_po_lead_time", 0)
                    )
                    lead_days += int(no_po_lead_time)

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
