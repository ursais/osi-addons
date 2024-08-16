# Import Odoo libs
from odoo import models


class ProductAttributeValue(models.Model):
    """Inherit Product Attribute Value for Method Overriding."""

    _inherit = "product.attribute.value"

    def _compute_display_name(self):
        # Call the parent class's _compute_display_name method to ensure any existing
        # logic is preserved.
        super()._compute_display_name()

        # Check if the context includes the "show_price_extra" key and its value
        # is True.
        if self._context.get("show_price_extra"):
            for rec in self:
                # Determine the quantity available for the associated product.
                # If there's no product associated, qty_available defaults to 0.
                qty_available = rec.product_id and rec.product_id.qty_available or 0

                # Calculate the on-hand quantity after subtracting outgoing quantities.
                # If there's no product, outgoing_qty defaults to 0.0.
                outgoing_qty = (
                    rec.product_id
                    and qty_available - rec.product_id.outgoing_qty
                    or 0.0
                )

                # Retrieve the product's state name if available, otherwise,
                # default to an empty string.
                product_state_string = (
                    rec.product_id and rec.product_id.product_state_id.name or ""
                )

                # Create a new display name with the format:
                # "Original Display Name (A:<qty_available>/OH:<outgoing_qty>)
                # (<product_state_string>)"
                new_name = f"{rec.display_name} (A:{qty_available}/OH:{outgoing_qty}) ({product_state_string})"

                # Update the record's display name only if a product is associated
                # with it.
                rec.display_name = rec.product_id and new_name or rec.display_name
