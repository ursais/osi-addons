# Import Odoo libs
from odoo import api, fields, models


class ProductAttributeValue(models.Model):
    """Inherit Product Attribute Value for Method Overriding."""

    _inherit = "product.attribute.value"

    # COLUMNS ##########

    qty_available = fields.Float(
        string="Qty On Hand",
        compute="_compute_quantities",
    )
    outgoing_qty = fields.Float(
        string="Qty Available",
        compute="_compute_quantities",
    )

    # END ##########
    # METHODS ##########

    @api.depends("product_id")
    def _compute_quantities(self):
        """Compute the quantity available and outgoing quantities."""
        for rec in self:
            if rec.product_id:
                rec.qty_available = rec.product_id.qty_available or 0
                rec.outgoing_qty = (
                    rec.qty_available - rec.product_id.outgoing_qty or 0.0
                )
            else:
                rec.qty_available = 0.0
                rec.outgoing_qty = 0.0

    def _compute_display_name(self):
        # Call the parent class's _compute_display_name method to ensure any existing
        # logic is preserved.
        super()._compute_display_name()

        # Check if the context includes the "show_price_extra" key and its value
        # is True.
        if self._context.get("show_price_extra"):
            product_template_id = self._context.get("active_id", False)
            price_precision = self.env["decimal.precision"].precision_get(
                "Product Price"
            )

            for rec in self:
                if rec.product_id:
                    # Start with product name instead of display_name
                    name = rec.product_id.name

                    # Add price extra if applicable (same as core method)
                    extra_prices = rec.get_attribute_value_extra_prices(
                        product_tmpl_id=product_template_id, pt_attr_value_ids=rec
                    )
                    price_extra = extra_prices.get(rec.id)
                    if price_extra:
                        name = f"{name} (+{price_extra:.{price_precision}f})"

                    # Build A/OH only for storable products
                    stock_info = ""
                    if rec.product_id.type == "product":
                        qty_available = rec.product_id.qty_available or 0
                        outgoing_qty = qty_available - rec.product_id.outgoing_qty or 0
                        stock_info = f"(A:{outgoing_qty}/OH:{qty_available}) "

                    # Product state
                    product_state_string = rec.product_id.product_state_id.name or ""

                    # Build display name with or without default_code
                    if rec.product_id.default_code:
                        rec.display_name = (
                            f"[{rec.product_id.default_code}] {name} "
                            f"{stock_info}({product_state_string})"
                        )
                    else:
                        rec.display_name = (
                            f"{name} {stock_info}({product_state_string})"
                        )

    # END ##########
