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
                line.customer_lead = 0
            else:
                line.order_id._set_dynamic_lead_times()

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
                line.order_id._set_dynamic_lead_times()
        return res

    def write(self, vals):
        """
        If the product_id is being changed either by user or re-configure
        product wizard we recompute the lead time.
        """
        res = super().write(vals)

        for line in self:
            if any(k in vals for k in ["product_id", "product_uom_qty", "bom_id"]):
                line.order_id._set_dynamic_lead_times()
        return res
