# Import Odoo libs
from odoo import fields, models
from odoo.exceptions import ValidationError


class ExceptionIgnore(models.Model):
    """
    New object that tracks which exceptions have been ignored on the record.
    This allows security group control on the exception rules.
    """

    _name = "exception.ignore"
    _description = "Per-Exception Ignore Flag"
    _rec_name = "exception_rule_id"

    # COLUMNS ######

    res_model = fields.Char(required=True)
    res_id = fields.Integer(
        string="Res ID",
        required=True,
        ondelete="cascade",
    )
    exception_rule_id = fields.Many2one(
        comodel_name="exception.rule",
        required=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        default=lambda self: self.env.uid,
    )

    # END ##########
    # CONSTRAINT ###

    _sql_constraints = [
        (
            "unique_ignore",
            "unique(res_model, res_id, exception_rule_id)",
            "Ignore entry already exists.",
        )
    ]

    # END ##########
    # METHODS ######
    def unlink(self):
        res_model_ids = {(r.res_model, r.res_id) for r in self}
        result = super().unlink()

        # Run detect_exceptions once per model, unless explicitly skipped
        if not self.env.context.get("skip_detect_exceptions"):
            for model_name, ids in self._group_records_by_model(res_model_ids):
                model = self.env[model_name].browse(ids)
                model.with_context(skip_detect_exceptions=True).detect_exceptions()

        return result

    def _group_records_by_model(self, res_model_ids):
        """Helper: {model: [ids]}"""
        from collections import defaultdict

        grouped = defaultdict(list)
        for model, res_id in res_model_ids:
            grouped[model].append(res_id)
        return grouped.items()

    # END ##########
