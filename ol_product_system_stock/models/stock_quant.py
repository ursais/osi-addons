# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    """
    Add a resend trigger when a quant changes
    """

    _inherit = "stock.quant"

    def get_product_resend_trigger_fields(self):
        """
        The fields of a `stock.quant` that should trigger a Webhook Request for the related product
        @return: list
        """
        return ["product_id", "location_id", "quantity"]

    @api.model
    def create(self, vals_list):
        """
        Always trigger a Webhook Request for the related product when a quant is created
        """
        res = super().create(vals_list)
        res.call_stock_change_response_functions()
        return res

    def write(self, vals):
        """
        Always trigger a Webhook Request for the related product when certain fields change on a quant
        """
        res = super().write(vals)

        trigger_fields = self.get_product_resend_trigger_fields()
        if any(key in trigger_fields for key in vals.keys()):
            self.call_stock_change_response_functions()

        return res

    def get_stock_change_response_products(self):
        """
        Find stock.quant related products that should be included
        in any integration communication as well
        """
        components = self.mapped("product_id")

        # Get all related Phantom BOMs (mrp.bom)
        phantom_bom_ids = components.get_related_phantom_bom_ids()

        phantom_kits = self.env["product.product"]
        # Get all related Phantom Kits (product.product)
        for bom in phantom_bom_ids:
            phantom_kits |= bom.product_id or bom.product_tmpl_id.product_variant_id

        # Components and Phantom Kits together(product.product)
        products = components | phantom_kits

        # Force filter out systems
        products = products.filtered(lambda p: not p.has_configurable_attributes)

        return products.mapped("product_tmpl_id")

    def call_stock_change_response_functions(self):
        """
        Call different functions if a products `On hand Qty` changes.
        """

        # Get the valid location domain. Core Odoo uses this in `addons/stock/models/product.py -> _compute_quantities_dict`
        domain_quant_loc, _, __ = self.env["product.product"]._get_domain_locations()

        for quant in self:

            if not self.search([("id", "=", quant.id)] + domain_quant_loc):
                # We only care about Quants that would affect the On Hand Qty of the related product
                # Core Odoo uses this in `addons/stock/models/product.py -> _compute_quantities_dict`
                _logger.debug(
                    f"Product Stock Message | Skip quant as location `{quant.location_id.name}` is not"
                    " eligible!"
                )
                continue

            if not quant.product_id.is_stockable():
                # We only care about stockable products
                _logger.debug(
                    "Product Stock Message | Skip quant as product is not stockable!"
                )
                continue

            # Get the queue jobs unique identifier
            identity_key = quant.get_identity_key()

            channel = self.env.ref("ol_webhooks.channel_webhook").complete_name

            # We use delayed queue.jobs for this to not affect the normal user actions
            # We add a 60 second delay to stack up queue.jobs for the same stock quant
            # and to allow Odoo to finish any long running processes to finish
            quant.with_delay(
                eta=60, max_retries=1, identity_key=identity_key, channel=channel
            ).delayed_call_stock_change_response_functions(company=quant.env.company)

    def get_identity_key(self):
        """
        Create the queue identify key by hashing the key values of the webhook
        """
        data = {
            "product": self.product_id.id,
            "company": self.company_id.id,
        }
        return self.env["api"].generate_hmac_signature(key=str(self.id), data=data)

    def delayed_call_stock_change_response_functions(self, company):
        """
        Call related Product Template webhooks
        """

        components_and_kits = (
            self.with_user(company.company_user_id)
            .with_company(company.id)
            .get_stock_change_response_products()
        )

        components_and_kits.product_stock_queue_trigger()
        _logger.info(
            f"Product Stock Message | Send Webhook for Location: `{self.location_id.name}` and"
            f" Products: {components_and_kits}"
        )
