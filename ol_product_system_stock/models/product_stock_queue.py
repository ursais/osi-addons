# Import Python Libs
from datetime import datetime
import logging

# Import Odoo Libs
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductStockQueue(models.Model):
    """
    The model to keep track of incoming graphql mutations
    """

    _name = "product.stock.queue"
    _description = "Product Stock Queue"

    # COLUMNS ###
    company_id = fields.Many2one(
        string="Internal Company", comodel_name="res.company", readonly=True
    )
    product_id = fields.Many2one(
        string="Product", comodel_name="product.product", readonly=True
    )
    # END #######

    def add_new(self, components, company=False):
        """
        Create a new Stock Status queue entry for each component
        """

        # Default to the environments Company
        company = company or self.env.company

        for component in components:
            self.env["product.stock.queue"].create(
                {
                    "product_id": component.id,
                    "company_id": company.id,
                }
            )

    def run(self, systems=False):
        # Run this process for each company separately
        component_template_ids = []
        updated_portfolio_ids = []
        queued_items = self.env["product.stock.queue"]

        for onlogic_company in (
            self.env["res.company"].get_all().sorted(key=lambda c: c.id)
        ):
            env = api.Environment(self.env.cr, onlogic_company.company_user_id.id, {})
            start_time = datetime.now()

            if not systems:
                # If no specific systems were passed
                # find the queue items for the given onlogic company
                queued_items_for_company = env["product.stock.queue"].search(
                    [("company_id", "=", onlogic_company.id)]
                )

                # Keep track of all Queue records
                queued_items |= queued_items_for_company

                # Get the unique components from the queue items
                components = queued_items_for_company.mapped("product_id")

                if not components:
                    # If there are no components there is nothing to do
                    _logger.info(
                        f"[{onlogic_company.short_name.upper()}] Product Stock Queue | No Components found to process. Skipping"
                    )
                    continue

            if systems:
                # Use the provided systems
                systems_containing_components = env["product.template"].browse(
                    systems.ids
                )
            else:
                # Find the component templates
                component_template_ids += components.mapped("product_tmpl_id").ids
                # Get all systems containing these components
                systems_containing_components = (
                    components.get_systems_containing_these_components(onlogic_company)
                )

            # Filter for eligible systems
            eligible_systems = self.get_eligible_systems(systems_containing_components)

            if not eligible_systems:
                _logger.info(
                    f"[{onlogic_company.short_name.upper()}] Product Stock Queue | No Systems found to process. Skipping"
                )
                continue

            _logger.info(
                f"[{onlogic_company.short_name.upper()}] Product Stock Queue | Start update process of System Stock State value"
                f" for {len(eligible_systems)} systems"
            )
            # Update the records `system_stock_state` field if necessary
            updated_portfolios, data = eligible_systems.update_system_stock_state()

            _logger.info(
                f"[{onlogic_company.short_name.upper()}] Product Stock Queue | Finished updating System Stock State value for"
                f" {len(eligible_systems)} systems in: {datetime.now() - start_time}s |"
                f" {len(updated_portfolios)} system's values were updated"
            )

            # Collect the ids of these templates
            updated_portfolio_ids += updated_portfolios.ids

        # Delete the queue items we processed
        if queued_items:
            queued_items.unlink()

        # Trigger follow up functionality
        # We use sudo() and browse() as we want to get a unique list of products from all companies
        # First send Components
        self.env["product.template"].sudo().browse(
            component_template_ids
        ).stock_quantity_changed()
        # Than send Systems
        self.env["product.template"].sudo().browse(
            updated_portfolio_ids
        ).system_stock_quantity_changed()

    def get_eligible_systems(self, systems):
        """
        We only care about Portfolio Systems
        """
        return systems.filtered(lambda p: p.system_tier == "normal")
