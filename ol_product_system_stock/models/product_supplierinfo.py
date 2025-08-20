# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api

_logger = logging.getLogger(__name__)


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    def get_product_resend_trigger_fields(self):
        """
        The fields of a `product.supplierinfo` that should trigger a Webhook Request for the related product
        @return: list
        """
        return [
            "name",
            "product_tmpl_id",
            "sequence",
            "min_qty",
            "price",
            "company_id",
            "product_id",
            "delay",
        ]

    @api.model
    def create(self, vals_list):
        """
        Always trigger a Webhook Request for the related product when a SupplierInfo is created
        """
        res = super().create(vals_list)
        res.call_change_response_functions()
        return res

    def write(self, vals):
        """
        Always trigger a Webhook Request for the related product when certain fields change on a SupplierInfo
        """
        res = super().write(vals)

        trigger_fields = self.get_product_resend_trigger_fields()
        if any(key in trigger_fields for key in vals.keys()):
            self.call_change_response_functions()

        return res

    def call_change_response_functions(self):
        """
        Offload the call to the change response functions to a delayed queue.job
        """

        for supplier_info in self:

            # Get the queue jobs unique identifier
            identity_key = supplier_info.get_identity_key()

            channel = self.env.ref("ol_webhooks.channel_webhook").complete_name

            # We use delayed queue.jobs for this to not affect the normal user actions
            # We add a 60 second delay to stack up queue.jobs for the same stock quant
            # and to allow Odoo to finish any long running processes to finish
            supplier_info.with_delay(
                eta=60, max_retries=1, identity_key=identity_key, channel=channel
            ).delayed_call_change_response_functions(company=supplier_info.env.company)

    def get_identity_key(self):
        """
        Create the queue identify key by hashing the key values of the webhook
        """
        data = {
            "name": self.partner_id.id,
            "product": self.product_tmpl_id.id,
            "company": self.company_id.id,
        }
        return self.env["api"].generate_hmac_signature(key=str(self.id), data=data)

    def delayed_call_change_response_functions(self, company):
        """
        Call related Product Template webhooks
        """

        product = (
            self.with_user(company.company_user_id)
            .with_company(company.id)
            .product_tmpl_id
        )
        product.product_stock_queue_trigger()
        _logger.info(
            f"Product Stock Message | Send Webhook for Supplier Info: `{self.partner_id.name}` and"
            f" Products: {product}"
        )
