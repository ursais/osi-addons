from odoo import fields, models


class AddManufacturingOrderWizard(models.TransientModel):
    _name = "add.manufacturing.order.wizard"
    _description = "Wizard to Add Manufacturing Orders to Batch"

    batch_id = fields.Many2one(
        "mrp.production.batch",
        string="Batch",
        required=True,
    )
    production_ids = fields.Many2many(
        "mrp.production",
        string="Manufacturing Orders",
        domain="[('state', 'not in', ('cancel','done','to_close','progress')),('mrp_batch_id', '=', False)]",
    )

    def action_add_to_batch(self):
        """Link the selected MOs to the batch's production_ids."""
        self.ensure_one()
        for production in self.production_ids:
            production.mrp_batch_id = self.batch_id.id
