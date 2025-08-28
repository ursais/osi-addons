from odoo import api, fields, models


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    @api.depends("product_id", "original_uom_qty")
    def _compute_customer_lead(self):
        for line in self:
            if not line.product_id:
                continue
            elif line.bom_id:
                lead_time = line._get_bom_lead_time()
            else:
                lead_time = line._get_standard_lead_time()
            line.customer_lead = lead_time

    def _get_bom_lead_time(self):
        """
        Fetch lead time from the BOM overview report based on max component delay +
        main product lead time.
        """
        self.ensure_one()

        bom_data = self.env["report.mrp.report_bom_structure"]._get_report_data(
            self.bom_id.id
        )

        # Get components list from the BOM data
        components = bom_data.get("lines", {}).get("components", [])

        if not components:
            # Default lead time if no components are found
            return 1

        # Get max delay from BOM components
        max_component_delay = self.env[
            "report.mrp.report_bom_structure"
        ]._get_max_component_delay(components)

        if max_component_delay is False:
            # No resupply possible
            return 0

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
        if available_qty >= self.original_uom_qty:
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
                "default_searchQty": self.original_uom_qty,
                "activate_availabilities": True
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sale blanket order lines created from the product configurator won't
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
            if "product_id" in vals:
                line._compute_customer_lead()
        return res
