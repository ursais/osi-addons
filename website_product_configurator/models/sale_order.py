import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update_order_line(self, product_id, quantity, order_line, **kwargs):
        """Inherit: To update the context of sale order line."""
        self.ensure_one()
        product_variant = self.env["product.product"].browse(product_id)
        # Retrieve the config session ID from the keyword arguments.
        config_session_id = kwargs.get("config_session_id", False)
        if not config_session_id and order_line and product_variant.config_ok:
            # If the config session ID is not provided and line ID is given,
            # find the corresponding order line and retrieve the config
            # session ID.
            order_line = self._cart_find_product_line(
                product_id, order_line.id, **kwargs
            )[:1]
            config_session_id = order_line.config_session_id.id

        ctx = {}
        # Convert config session ID to integer if it exists.
        if config_session_id and product_variant.config_ok:
            config_session_id = int(config_session_id)
            # Set the context with config session ID and current sale line.
            ctx = {
                "current_sale_line": order_line.id,
                "default_config_session_id": config_session_id,
            }

        return super(SaleOrder, self.with_context(**ctx))._cart_update_order_line(
            product_id, quantity=quantity, order_line=order_line, **kwargs
        )

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        """Include Config session in search."""
        order_line = super()._cart_find_product_line(
            product_id=product_id, line_id=line_id, **kwargs
        )
        # Check if config_session_id is provided.
        config_session_id = kwargs.get("config_session_id", False)

        # If a line ID is provided, return the initial product line.
        if not config_session_id or not config_session_id.isdigit():
            # Return the original order line if config_session_id is undefinded.
            return order_line

        # Filter the product line based on the config_session_id.
        order_line = order_line.filtered(
            lambda p: p.config_session_id.id == int(config_session_id)
        )
        return order_line

    def _prepare_order_line_values(
        self,
        product_id,
        quantity,
        linked_line_id=False,
        no_variant_attribute_values=None,
        product_custom_attribute_values=None,
        **kwargs,
    ):
        """Inherit: Skip the creating product_variant based on received_combination for
        the configurable products."""
        self.ensure_one()
        product = self.env["product.product"].browse(product_id)
        if not product.product_tmpl_id.config_ok:
            return super()._prepare_order_line_values(
                product_id=product_id,
                quantity=quantity,
                linked_line_id=linked_line_id,
                no_variant_attribute_values=no_variant_attribute_values,
                product_custom_attribute_values=product_custom_attribute_values,
                kwargs=kwargs,
            )
        values = {
            "product_id": product.id,
            "product_uom_qty": quantity,
            "order_id": self.id,
            "linked_line_id": linked_line_id,
        }
        return values
