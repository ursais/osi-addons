# Import Odoo libs
from odoo import fields, models
from odoo.exceptions import UserError


class MRPProductionBatchwizard(models.TransientModel):
    """Wizard Object for allow Add to/Create Batch from list view."""

    _name = "mrp.production.batch.wizard"
    _description = "Wizard to Add MO to Batch or Create a New Batch"

    # COLUMNS #########

    batch_id = fields.Many2one("mrp.production.batch")
    responsible_id = fields.Many2one("res.users", string="Responsible")
    tag_ids = fields.Many2many("mrp.production.batch.tag", string="Tags")
    date_start = fields.Datetime(string="Scheduled Date")

    # END #########
    # METHODS #####

    def action_confirm(self):
        """Method on wizard to either add the selected MO's to an existing Batch or
        create a new Batch."""
        active_ids = self._context.get("active_ids")
        records = self.env["mrp.production"].browse(active_ids)
        allowed_records = records.filtered(lambda m: m.state in ["confirmed", "draft"])

        if not allowed_records:
            # Raise Error if no MO's can be added to a batch
            raise UserError("No Qualified MO's can be added to a Batch.")
        if not self.batch_id:
            # If no batch selected in the wizard then create a new one.
            vals = {
                "responsible_id": self.responsible_id.id,
                "tag_ids": self.tag_ids.ids,
                "date_start": self.date_start,
                "production_ids": allowed_records,
            }
            self.env["mrp.production.batch"].create(vals)
        else:
            # If batch is set in wizard then add MO's to existing Batch.
            allowed_records.write({"mrp_batch_id": self.batch_id.id})

    # END #########
