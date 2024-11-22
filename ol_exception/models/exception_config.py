from odoo import models, fields


class ExceptionConfig(models.Model):
    _name = "exception.config"
    _description = "Exception Configuration"

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        ondelete="cascade",
    )
    trigger_field_ids = fields.Many2many(
        "ir.model.fields",
        domain="[('model_id', '=', model_id),('store', '=', True)]",
        string="Fields to Trigger Exception Checks",
        help="When any of the fields in this list change, they will trigger an exception check on the model.",
    )

    _sql_constraints = [
        (
            "unique_model_id",
            "unique(model_id)",
            "Only one exception configuration per model is allowed.",
        )
    ]
