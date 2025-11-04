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
    reason_code_id = fields.Many2one(
        comodel_name="scrap.reason.code",
        string="Reason Code",
    )
    note = fields.Char(string="note")

    # END #######
    # METHODS ###

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))

    # END #######

    reason_code_id_domain = fields.Binary(
        string="Reason Code Domain",
        compute="_compute_reason_code_id_domain",
        store=False,
    )

    @api.depends("repair_batch_id", "repair_batch_id.company_id")
    def _compute_reason_code_id_domain(self):
        """Compute domain for reason_code_id based on parent batch company."""
        for line in self:
            if line.repair_batch_id and line.repair_batch_id.company_id:
                line.reason_code_id_domain = [
                    ("|"),
                    ("company_id", "=", False),
                    ("company_id", "=", line.repair_batch_id.company_id.id),
                ]
            else:
                line.reason_code_id_domain = []

