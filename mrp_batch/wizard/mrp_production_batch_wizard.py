from odoo import fields, models
from odoo.exceptions import UserError


class MRPProductionBatchwizard(models.TransientModel):
    _name = "mrp.production.batch.wizard"

    batch_id = fields.Many2one("mrp.production.batch")
    responsible_id = fields.Many2one("res.users", string="Responsible")
    tag_ids = fields.Many2many("mrp.production.batch.tag", string="Tags")
    date_scheduled = fields.Datetime(string="Scheduled Date")

    def action_confirm(self):
        active_ids = self._context.get("active_ids")
        records = self.env["mrp.production"].browse(active_ids)
        allowed_records = records.filtered(lambda m: m.state in ["confirmed", "draft"])

        if not allowed_records:
            raise UserError("No Qualified MO's can be added to a Batch.")
        if not self.batch_id:
            vals = {
                "responsible_id": self.responsible_id.id,
                "tag_ids": self.tag_ids.ids,
                "date_scheduled": self.date_scheduled,
                "production_ids": allowed_records,
            }
            self.env["mrp.production.batch"].create(vals)
        else:
            allowed_records.write({"mrp_batch_id": self.batch_id.id})
