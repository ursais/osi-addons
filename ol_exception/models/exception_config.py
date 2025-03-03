# Import Odoo libs
from odoo import models, fields


class ExceptionConfig(models.Model):
    """
    Currently the exception checks are triggered either via specific methods or
    scheduled actions. This adds a new object for configurating 'Trigger Fields' which
    can then be used to trigger the exception checks if that field is being updated.
    This was a configurable solution to not triggering exception checks consistantly.
    """

    _name = "exception.config"
    _description = "Exception Configuration"

    # COLUMNS ######

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

    # END ##########
    # METHODS ##########

    def get_related_fields(self):
        """
        Returns a dictionary of fields related to trigger_field_ids for the configured model.
        """
        self.ensure_one()  # Ensure we are operating on a single record
        # sudo is used in search as non-admins don't have direct access to ir.model
        related_fields = (
            self.env["ir.model.fields"]
            .sudo()
            .search(
                [
                    ("ttype", "=", "related"),
                    ("related", "!=", False),
                    (
                        "model_id",
                        "!=",
                        self.model_id.id,
                    ),  # Related fields in other models
                    ("related", "ilike", f"{self.model_id.model}.%"),
                ]
            )
        )
        # Filter fields that are directly related to trigger fields
        trigger_field_names = {field.name for field in self.trigger_field_ids}
        return [
            field
            for field in related_fields
            if field.related.split(".", 1)[1] in trigger_field_names
        ]

    def get_field_mapping(self):
        """
        Returns a mapping of current model fields to related fields in other models,
        considering only models that have `exception.config` records.
        Example: {'locked': ['sale_locked']}
        """
        self.ensure_one()

        # Get trigger field names
        trigger_field_names = self.trigger_field_ids.mapped("name")

        # Get models that have exception.config records
        # sudo is used as non-admins don't have direct access to ir.model
        exception_models = (
            self.env["exception.config"].sudo().search([]).mapped("model_id.model")
        )

        # Find related fields pointing to this model's fields, limited to models with exception configs
        related_fields = (
            self.env["ir.model.fields"]
            .sudo()
            .search(
                [
                    ("related", "!=", False),
                    (
                        "model_id.model",
                        "in",
                        exception_models,
                    ),  # Only consider models with exception configs
                ]
            )
        )
        field_mapping = {}
        for field in related_fields:
            # Extract the final field in the related path
            related_target = field.related.split(".")[
                -1
            ]  # Get the last part of the path
            if related_target in trigger_field_names:
                field_mapping.setdefault(related_target, []).append(field.name)

        return field_mapping

    # END ##########
