# Import Odoo libs
from odoo import models, api


class StockMove(models.Model):
    """
    Override stock moves to set sale_line_id for mrp uses and ensure
    kit component quantities are correctly set.
    """

    _inherit = "stock.move"

    # Methods #####

    def _prepare_procurement_values(self):
        # Ensure sale_line_id is propagated through stock moves
        res = super()._prepare_procurement_values()
        if self.sale_line_id:
            # Pass sale_line_id into procurement values
            res["sale_line_id"] = self.sale_line_id.id
        return res

    def _action_assign(self):
        """
        Override _action_assign to ensure kit component quantities are correctly
        set before checking availability. This fixes the issue where kit SKUs
        don't populate quantities on Delivery Orders when 'Check Availability' is clicked.
        
        This method identifies moves from kit products (phantom BOMs) and ensures
        their quantities are correctly calculated as: BOM line quantity * kit quantity ordered.
        """
        # First, ensure quantities are correct for kit components
        moves_to_check = self.filtered(
            lambda m: m.picking_id 
            and m.picking_id.sale_id 
            and m.product_uom_qty == 0
            and m.state in ('waiting', 'confirmed', 'partially_available')
        )
        
        if moves_to_check:
            # Group moves by picking to avoid duplicate BOM lookups
            pickings = moves_to_check.mapped('picking_id')
            
            for picking in pickings:
                sale_order = picking.sale_id
                if not sale_order:
                    continue
                
                # Get all kit products from the sale order and calculate component quantities
                kit_components = {}
                for sale_line in sale_order.order_line:
                    if sale_line.product_id:
                        bom = self.env['mrp.bom']._bom_find(
                            sale_line.product_id,
                            picking_type=picking.picking_type_id,
                            company_id=picking.company_id.id
                        )[0]
                        
                        if bom and bom.type == 'phantom':
                            kit_qty = sale_line.product_uom_qty or sale_line.product_qty or 0
                            # Calculate quantities for each component in this kit
                            for bom_line in bom.bom_line_ids:
                                component_id = bom_line.product_id.id
                                bom_line_qty = bom_line.product_qty or 0
                                calculated_qty = bom_line_qty * kit_qty
                                
                                # Sum quantities if component appears in multiple kits
                                if component_id not in kit_components:
                                    kit_components[component_id] = calculated_qty
                                else:
                                    kit_components[component_id] += calculated_qty
                
                # Update moves with correct quantities
                for move in moves_to_check.filtered(lambda m: m.picking_id == picking):
                    if move.product_id.id in kit_components:
                        correct_qty = kit_components[move.product_id.id]
                        if move.product_uom_qty != correct_qty:
                            move.write({'product_uom_qty': correct_qty})
        
        # Call parent method to perform availability check
        return super()._action_assign()

    # END #########
