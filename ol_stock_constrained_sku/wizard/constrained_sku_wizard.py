# Import Python libs
import base64
import logging

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import models, fields, api


class ConstrainedSkuWizard(models.TransientModel):
    _name = "constrained.sku.wizard"
    _description = "Constrained SKU Wizard"

    # COLUMNS #####

    allowed_component_ids = fields.Many2many(
        string="Allowed SKUs",
        comodel_name="product.product",
        relation="constrained_sku_wizard_allowed_products_rel",
        column1="wizard_id",
        column2="product_id",
    )
    component_ids = fields.Many2many(
        string="SKUs",
        comodel_name="product.product",
        relation="constrained_sku_wizard_products_rel",
        column1="wizard_id",
        column2="product_id",
    )
    line_ids = fields.One2many(
        string="Lines",
        comodel_name="constrained.sku.wizard.line",
        inverse_name="wizard_id",
    )

    # END #########

    @api.model
    def default_get(self, fields):
        """
        Pre-load fields in the wizard with existing data
        """

        res = super().default_get(fields)
        # Update the wizard from the context data
        res["allowed_component_ids"] = self.env.context.get(
            "components", self.env["product.product"]
        )
        res["line_ids"] = [(0, 0, v) for v in self.env.context.get("lines_data", [])]
        return res

    def action_allocate_included(self):
        return self.run(allocate=True, included=True)

    def action_unallocate_included(self):
        return self.run(allocate=False, included=True)

    def action_allocate_excluded(self):
        return self.run(allocate=True, included=False)

    def action_unallocate_excluded(self):
        return self.run(allocate=False, included=False)

    def run(self, allocate, included):
        """
        Get the eligible Stock Moves based on the Sale orders and the selected components
        """

        # determine if the move got full, partial or no stock allocation
        def get_indicator(move):
            if move.quantity == move.product_uom_qty:
                return "✅"
            elif move.quantity == 0:
                return "❌"
            return "⚠️"

        # We need to exclude different states based on if we want to allocate or not
        allowed_states = (
            ["assigned", "partially_available", "waiting", "confirmed"]
            if allocate
            else ["assigned", "partially_available"]
        )

        skipped_lines = []
        processed_lines = []
        for line in self.line_ids.sorted(key=lambda j: j.sequence):
            picking = line.picking_id
            # Loop over each picking one by one
            # This is important as the users could specific a priority list
            # between pickings via the wizard
            moves = self.env["stock.move"]
            for move in picking.mapped("move_ids"):  # Replaced move_lines with move_ids
                # Loop over each move one by one

                if move.product_id.has_configurable_attributes:
                    # Produced systems should be excluded
                    skipped_lines.append(
                        {
                            "sale_order_id": picking.sale_id.id,
                            "picking_id": picking.id,
                            "product_id": move.product_id.id,
                            "type": "skipped",
                            "skip_reason": "Product is a system",
                        }
                    )
                    continue

                # Check if the Stock Move's product is in the selected list or not
                move_product_in_selected = move.product_id in self.component_ids

                if (
                    # If we are looking for moves that include the selected components
                    # and the move's product is not in that list
                    (included and not move_product_in_selected)
                    # Or if we are looking for moves that do not include the selected components
                    # and the move's product is in that list
                    or (not included and move_product_in_selected)
                ):
                    # Skip the move
                    continue

                if move.state not in allowed_states:
                    # Move has the wrong state
                    skipped_lines.append(
                        {
                            "sale_order_id": picking.sale_id.id,
                            "picking_id": picking.id,
                            "product_id": move.product_id.id,
                            "type": "skipped",
                            "skip_reason": f"Stock Move state not allowed: {move.state}",
                        }
                    )
                    continue

                moves |= move

                # TODO: Because we are only processing the moves one by one (in order for the stock level indicator to be correct), there is potential for a speed improvement by rewriting the flow of this function so that we perform bulk actions.
                if allocate:
                    # Allocate the move
                    move._action_assign()
                else:
                    # Un-reserve the move
                    move._do_unreserve()

                processed_lines.append(
                    {
                        "sale_order_id": picking.sale_id.id,
                        "picking_id": picking.id,
                        "change_indicator": get_indicator(move),
                        "product_id": move.product_id.id,
                        "type": "processed",
                    }
                )

            if moves:
                self.add_chatter_message_to_picking(allocate, picking, moves)

        return {
            "type": "ir.actions.act_window",
            "res_model": "constrained.sku.result.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "allocate": allocate,
                "processed_lines": processed_lines,
                "skipped_lines": skipped_lines,
            },
        }

    def add_chatter_message_to_picking(self, allocate, picking, moves):
        """
        Add a chatter message to the related Stock Picking to keep track of changes
        """
        msg = f"""
                Constrained SKU Bulk action was used to {'allocate' if allocate else 'unallocate'} stock for these SKUs<br/>
                <ul>
                """
        for move in moves:
            msg += f"""
            <li>
               <a href=# data-oe-model=product.product data-oe-id={move.product_id.id}>{move.product_id.default_code}</a> | Stock Move <a href=# data-oe-model=stock.move data-oe-id={move.id}>{move.display_name}</a>.
            </li>
            """
        msg += f"""<ul><br/>User: {self.env.user.name}"""
        picking.message_post(body=msg)
        _logger.info(msg)


class ConstrainedSkuWizardLine(models.TransientModel):
    _name = "constrained.sku.wizard.line"
    _description = "Constrained SKU Wizard Line"

    wizard_id = fields.Many2one(comodel_name="constrained.sku.wizard")
    sequence = fields.Integer(
        string="Priority", help="Priority of the line", default=10
    )
    sale_order_id = fields.Many2one(
        string="Sale Order",
        comodel_name="sale.order",
        domain="[('state', 'not in', ['done', 'draft', 'cancel'])]",
    )
    picking_id = fields.Many2one(
        string="Transfer",
        comodel_name="stock.picking",
    )

    # END #########
