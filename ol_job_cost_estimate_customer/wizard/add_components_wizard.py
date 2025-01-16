# Import Odoo libs
from odoo import Command, fields, models


class AddComponentsWizard(models.TransientModel):
    _name = "add.components.wizard"
    _description = "Wizard to Add Components"

    # COLUMNS #####

    product_id = fields.Many2one(
        "product.product",
        domain=[("bom_ids", "!=", False)],
    )

    # END #########

    # METHODS #####

    def action_add_components(self):
        self.ensure_one()
        # Retrieve the active sale estimate job using the context
        sale_estimate_job = self.env["sale.estimate.job"].browse(
            self._context.get("active_id")
        )
        # Filter the Bill of Materials (BOM) associated with the product
        # Exclude scaffolding BOMs and BOMs without a product
        bom_ids = self.product_id.bom_ids.filtered(
            lambda l: not l.scaffolding_bom and l.product_id
        )
        # If no valid BOMs are found, create an empty recordset
        bom_ids = bom_ids and bom_ids[0] or self.env["mrp.bom"]
        for bom_line in bom_ids.bom_line_ids:
            # Create a new estimate line to the sale estimate job
            sale_estimate_job.estimate_ids = [
                Command.create(
                    {
                        "job_type": "material",
                        "product_id": bom_line.product_id.id,
                        "product_uom_qty": bom_line.product_qty,
                        "product_uom": bom_line.product_uom_id.id,
                    }
                )
            ]

        # Set Unit Price on lines based on pricelist
        sale_estimate_job.action_update_prices()

        return True

    # END #########
