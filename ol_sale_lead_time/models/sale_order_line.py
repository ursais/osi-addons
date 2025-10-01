from datetime import timedelta
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    available_date = fields.Date(
        string="Available Date",
        compute="_compute_available_date",
    )

    @api.depends("order_id.date_order", "customer_lead")
    def _compute_available_date(self):
        for line in self:
            base_date = line.order_id.date_order.date() or field.Date.today()
            if line.customer_lead:
                line.available_date = base_date + timedelta(days=line.customer_lead)
            else:
                line.available_date = base_date

    @api.depends("product_id", "product_uom_qty")
    def _compute_customer_lead(self):
        for line in self:
            if not line.product_id:
                continue
            else:
                line._set_dynamic_lead_times()
            # elif line.bom_id:
            #     lead_time = line._get_bom_lead_time()
            # else:
            #     lead_time = line._get_standard_lead_time()
            # line.customer_lead = lead_time
    
    def _set_dynamic_lead_times(self):
        """Compute customer_lead for all lines in this order,
        considering shared BOM components and availability."""
        today = fields.Date.today()

        for order in self:
            # --- Step 1: Build component requirements map ---
            component_demand = {}   # {product_id: total_qty}
            line_components = {}    # {line_id: [product_id, ...]}

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
                product_avail[product_id] = avail_date

            # --- Step 3: Assign line-level customer_lead ---
            for line in order.order_line:
                if not line_components[line.id]:
                    line.customer_lead = 0
                    continue

                comp_dates = [product_avail[pid] for pid in line_components[line.id]]
                base_date = max(comp_dates)

                lead_days = (base_date - today).days

                # Add rush/manufacturing delays
                if order.is_rush_order:
                    rush_days = int(
                        self.env["ir.config_parameter"].sudo().get_param("onl.rush_lead_days", 0)
                    )
                    lead_days += rush_days
                else:
                    lead_days += line.product_id.produce_delay
                    mfg_sec = int(
                        self.env["ir.config_parameter"].sudo().get_param("stock.manufacturing_lead_security", 0)
                    )
                    lead_days += mfg_sec

                line.customer_lead = max(0, lead_days)


    def _get_bom_lead_time(self):
        """Fetch lead time from the BOM overview report based on max component delay + main product lead time."""
        self.ensure_one()

        bom_data = self.env["report.mrp.report_bom_structure"]._get_report_data(
            self.bom_id.id
        )

        # Get components list from the BOM data
        components = bom_data.get("lines", {}).get("components", [])

        if not components:
            return 1  # Default lead time if no components are found

        # Get max delay from BOM components
        max_component_delay = self.env[
            "report.mrp.report_bom_structure"
        ]._get_max_component_delay(components)

        if max_component_delay is False:
            return 0  # No resupply possible

        # Get the lead time of the top-level product (main component)
        top_component_lead_time = bom_data.get("lines", {}).get("lead_time", 0)

        # Total lead time = max component delay + top-level product lead time
        total_lead_time = max_component_delay + top_component_lead_time

        return max(total_lead_time, 1)  # Ensure at least 1 day lead time

    def _get_standard_lead_time(self):
        """Fallback lead time if no BOM is found."""
        self.ensure_one()
        available_qty = self.product_id.with_context(
            to_date=fields.Date.today()
        ).virtual_available
        if available_qty >= self.product_uom_qty:
            return max(self.product_id.sale_delay, 1)
        vendor = self.product_id.seller_ids and self.product_id.seller_ids[0]
        return vendor.delay if vendor else 1

    def action_open_bom_overview(self):
        """Open the BoM Overview report for the selected BoM."""
        self.ensure_one()
        if not self.bom_id:
            return False

        return {
            "type": "ir.actions.client",
            "tag": "mrp_bom_report",
            "name": "BoM Overview",
            "context": {
                "model": "report.mrp.report_bom_structure",
                "active_id": self.bom_id.id,
                "active_ids": [self.bom_id.id],
                "default_searchQty": self.product_uom_qty,
                "activate_availabilities": True,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sale order lines created from the product configurator won't
        trigger lead compute so we can do so in create method.
        """
        res = super().create(vals_list)
        for line in res:
            if line.config_session_id:
                line._compute_customer_lead()
        return res

    def write(self, vals):
        """
        If the product_id is being changed either by user or re-configure
        product wizard we recompute the lead time.
        """
        res = super().write(vals)

        for line in self:
            if any(k in vals for k in ["product_id", "product_uom_qty", "bom_id"]):
                line._compute_customer_lead()
        return res
