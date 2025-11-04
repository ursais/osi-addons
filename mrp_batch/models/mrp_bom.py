# Import Odoo libs
from odoo import api, models


class MrpBom(models.Model):
    """Inherit BoM to add default delay and prepare values."""

    _inherit = "mrp.bom"

    # METHODS #####

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        default_produce_delay = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.default_produce_delay")
        )
        default_days_to_prepare_mo = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.default_days_to_prepare_mo")
        )
        if default_produce_delay:
            defaults.update({"produce_delay": default_produce_delay})
        if default_days_to_prepare_mo:
            defaults.update({"days_to_prepare_mo": default_days_to_prepare_mo})

        return defaults

    def explode(self, product, quantity, picking_type=None):
        """
        Override explode to ensure component quantities are correctly
        calculated for kit SKUs (phantom BOMs) when expanding into delivery orders.

        This method ensures that when a kit product has components with quantities
        greater than 1 in the BOM, those quantities are properly multiplied by the
        kit quantity being ordered.

        Args:
            product: Product to explode
            quantity: Quantity of the kit product to explode
            picking_type: Stock picking type (optional)

        Returns:
            List of tuples containing (component_dict, bom_line) for each component
        """
        # Call parent method to get base explosion
        result = super().explode(product, quantity, picking_type)

        # For phantom BOMs (kit products), ensure component quantities are correctly calculated
        if self.type == 'phantom':
            # Process each component in the explosion result
            for component_data, bom_line in result:
                if component_data and bom_line:
                    # Calculate the correct quantity: BOM line qty * kit quantity
                    bom_line_qty = bom_line.product_qty or 0
                    calculated_qty = bom_line_qty * quantity
                    
                    # Update component data with correct quantity
                    if component_data.get('product_qty') != calculated_qty:
                        component_data['product_qty'] = calculated_qty
                    
                    # Also ensure product_uom_qty is set correctly
                    if 'product_uom_qty' in component_data:
                        component_data['product_uom_qty'] = calculated_qty
                    elif 'product_uom' in component_data:
                        # If UOM is specified, ensure quantity matches
                        component_data['product_uom_qty'] = calculated_qty

        return result

    # END #########
