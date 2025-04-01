# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairBatchLine(models.Model):
    _name = "repair.batch.line"
    _description = "Repair Batch Line"

    # COLUMNS ###

    repair_batch_id = fields.Many2one(
        comodel_name="repair.batch",
        string="Repair Batch",
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
    )
    repair_line_type = fields.Selection(
        [
            ("add", "Add"),
            ("remove", "Remove"),
            ("recycle", "Recycle"),
        ],
        string="Type",
        required=True,
    )

    # END #######
    # METHODS ###

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))

    # END #######
